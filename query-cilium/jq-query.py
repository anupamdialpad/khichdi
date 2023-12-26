# Object oriented style filtering the backend pods queried by using the `cilium` binary inside the pod
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(filename)s:%(lineno)d %(levelname)s - %(message)s')

class CiliumContext:
    def __init__(self, cilium_cmd_class):
        self.container_id = self.fetch_container_id()
        self.cilium_cmd_class = cilium_cmd_class
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def command(self, cmd): # must return a new instance
        cilium_cmd = self.cilium_cmd_class('crictl exec -s %s %s' % (self.container_id, cmd))
        return cilium_cmd
    
    def services(self):
        return self.command('cilium service list').each()
    
    def service(self, service_id):
        return self.command('cilium service get %s' % service_id)
    
    @property
    def frontend_ip(self):
        return CiliumJqSelect().filter('.spec["frontend-address"].ip')
    
    def fetch_container_id(self): # return container id of cilium
        return 'e21b5e13f9629'
    
class JqCommand:
    def __init__(self, cmd):
        self.cmd = cmd + ' -o json'
        self.pipe_cmds = []
    
    def fetch(self, query):
        self.pipe_cmds.append(query)
        return self
    
    def select(self, jq_select):
        self.pipe_cmds.append(str(jq_select))
        return self

    def execute(self):
        return str(self)
    
    def __str__(self):
        return "%s | jq -r '%s'" % (self.cmd, ' | '.join(self.pipe_cmds))
    
class JqSelect:
    def __init__(self):
        self.filters = []

    def filter(self, lhs):
        self.filters.append(lhs)
        return JqFilterOperator(self)
    
    def And(self):
        self.filters.append('and')
        return self
    
    def __str__(self):
        return 'select(%s)' % ' '.join(self.filters)
    
class JqFilterOperator:
    def __init__(self, jq_select):
        self.jq_select = jq_select

    def equals(self, rhs):
        lhs = self.jq_select.filters.pop()
        expression = '%s==%s' % (lhs, rhs)
        self.jq_select.filters.append(expression)
        return self.jq_select
    
class CiliumServiceJq(JqCommand):
    def __init__(self, cmd):
        super().__init__(cmd)

    def each(self):
        return self.fetch('.[]')
    
    def frontend_ip(self, ip):
        return self.filter('.spec["frontend-address"].ip', '"%s"' % ip).add().filter(
            '.spec["frontend-address"].scope', '"external"')
    
    def id(self):
        return self.fetch('.spec.id')
    
    def backend_addresses(self):
        return self.fetch('.status.realized["backend-addresses"]')

class CiliumJqSelect(JqSelect):
    def filter(self, lhs):
        self.filters.append(lhs)
        return CiliumJqFilterOperator(self)
    
class CiliumJqFilterOperator(JqFilterOperator):
    def equals(self, rhs):
        return super().equals('"%s"' % rhs)
    

run_command = JqCommand('cilium service list').fetch('.[].spec').select(JqSelect().filter( # .spec["frontend-address"].ip=="199.27.151.90" 
      '.["frontend-address"].ip').equals('"199.27.151.90"').And().filter( # and .spec["frontend-address"].scope=="external")
      '.["frontend-address"].scope').equals('"external"')).fetch('.id')
assert str(run_command) == 'cilium service list -o json | jq -r \'.[].spec | select(.["frontend-address"].ip=="199.27.151.90" and .["frontend-address"].scope=="external") | .id\''
run_command = JqCommand('cilium service list').fetch('.[].spec').select(JqSelect().filter(
      '.["frontend-address"].ip').equals('"199.27.151.90"')).select(JqSelect().filter(
      '.["frontend-address"].scope').equals('"external"')).fetch('.id')
assert str(run_command) == 'cilium service list -o json | jq -r \'.[].spec | select(.["frontend-address"].ip=="199.27.151.90") | select(.["frontend-address"].scope=="external") | .id\''

run_command = JqCommand('cilium service get 142').select(JqSelect().filter(
      '.spec["frontend-address"].ip').equals('"199.27.151.90"').And().filter(
      '.spec["frontend-address"].scope').equals('"external"')).fetch('.status.realized["backend-addresses"]')
assert str(run_command) == 'cilium service get 142 -o json | jq -r \'select(.spec["frontend-address"].ip=="199.27.151.90" and .spec["frontend-address"].scope=="external") | .status.realized["backend-addresses"]\''


service_id = 142
anycast_ip = '199.27.151.90'
with CiliumContext(CiliumServiceJq) as cilium:
    cmd = cilium.services().select(cilium.frontend_ip.equals(anycast_ip)).id()
    logging.info(cmd.execute())

    cmd = cilium.service(service_id).select(cilium.frontend_ip.equals(anycast_ip)).backend_addresses()
    logging.info(cmd.execute())
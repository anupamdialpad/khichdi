# Object oriented way of Json parsing

import logging
import sys
import json
import functools

from pathlib import Path

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(filename)s:%(lineno)d %(levelname)s - %(message)s')

def json_load(filename):
    service_list = Path(__file__).with_name(filename)
    with service_list.open('r') as f:
        return json.load(f)

def services():
    return json_load('service-list.json')

def cilium_service(service_id):
    return CiliumJsonDict(json_load('service-%s.json' % service_id))

def cilium_services():
    rows = [CiliumJsonDict(row) for row in services()]
    return CiliumJsonDictArray(rows)

def frontend_ip():
    return JsonSelect().filter(('spec', 'frontend-address', 'scope')).equals(
            'external').And().filter(('spec', 'frontend-address', 'ip'))

class JsonDict:
    def __init__(self, di=None):
        self.di = di

    def each(self):
        json_dicts = [JsonDict(di) for di in self.di]
        return JsonDictArray(json_dicts)

    def get(self, key_tuple):
        if self.di is None:
            return self.__class__()
        return self.__class__(functools.reduce(dict.get, key_tuple, self.di))

    # it is required to know when all the operations are done
    def select(self, json_select):
        op_results = []
        for operation in json_select.operations:
            op_results.append(operation.result(self.di) if isinstance(
                operation, JsonSelectOperation) else operation)

        evaluate = ' '.join(map(str, op_results))
        if eval(evaluate):
            return self
        return self.__class__()
    
    def __bool__(self):
        return self.di is not None
    
    def __str__(self):
        return json.dumps(self.di)

class JsonDictArray:
    def __init__(self, json_dicts):
        self.json_dicts = json_dicts

    def select(self, json_select):
        results = [json_dict.select(json_select) for json_dict in self.json_dicts]
        return self.__class__(results)
    
    def get(self, key_tuple):
        results = [json_dict.get(key_tuple) for json_dict in self.json_dicts]
        return self.__class__(results)
    
    def __str__(self):
        return json.dumps([json_dict.di for json_dict in self.json_dicts if json_dict])
    
class JsonSelect:
    def __init__(self):
        self.operations = []

    def filter(self, lhs):
        operation = JsonSelectOperation(self, lhs)
        self.operations.append(operation)
        return operation
    
    def And(self):
        self.operations.append('and')
        return self

class JsonSelectOperation:
    def __init__(self, jq_select, lhs):
        self.lhs = lhs
        self.json_select = jq_select

    def equals(self, rhs):
        self.rhs = rhs
        self.res = lambda di: functools.reduce(dict.get, self.lhs, di) == self.rhs
        return self.json_select
    
    def result(self, di):
        return self.res(di)

class CiliumJsonDict(JsonDict):
    def backend_addresses(self):
        return self.get(('spec', 'backend-addresses'))
    
    def active_backend(self, ip):
        backend_addresses = self.backend_addresses()
        json_dicts = [CiliumJsonDict(di) for di in backend_addresses.di]
        return CiliumJsonDictArray(json_dicts).select(JsonSelect().filter(('ip',)).equals(
            ip).And().filter(('state',)).equals('active'))

class CiliumJsonDictArray(JsonDictArray):
    def id(self):
        return self.get(('spec', 'id'))     

anycast_ip = '199.27.151.90'
service_id = 142
pod_ip = '10.68.5.180'
service_ids = []

service_id_json = JsonDict(services()).each().select(JsonSelect().filter(('spec', 'frontend-address', 'ip')).equals(anycast_ip).And().filter(('spec', 'frontend-address', 'scope')).equals('external')).get(('spec', 'id'))
service_ids = [str(service_id) for service_id in service_id_json.json_dicts if service_id]
assert sorted(service_ids) == ['142', '145'], service_ids

service_id_json = cilium_services().select(frontend_ip().equals(anycast_ip)).id()
service_ids = [str(service_id) for service_id in service_id_json.json_dicts if service_id]
assert sorted(service_ids) == ['142', '145'], service_ids


backend_addresses = cilium_service(service_id).select(frontend_ip().equals(anycast_ip)).backend_addresses()
logging.debug(backend_addresses)

backend_addresses = cilium_service(service_id).select(frontend_ip().equals(anycast_ip)).active_backend(pod_ip)
logging.debug(backend_addresses)

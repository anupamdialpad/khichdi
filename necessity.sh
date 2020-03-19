# if my machine
mine=0
if [[ $HOSTNAME =~ .*anupam.* ]]; then
  mine=1
fi

# enable bash completion
type _init_completion 2>/dev/null
if [[ $? != 0 ]]; then
  apt install bash-completion
fi

# check if kubectl is installed
if [[ `which kubectl` && ! -f /etc/bash_completion.d/kubectl ]]; then
  kubectl completion bash >/etc/bash_completion.d/kubectl
fi

if [[ $mine ]]; then
  cp ~/.bashrc ~/.bashrc.bak.`date +"%s"`
  cp ./.bashrc ~/.bashrc
  cp ./.vimrc ~/.vimrc
fi

echo "run: source ~/.bashrc"
#!/bin/bash

echo ${INTER_RUN_INTERVAL}

#add hosts to /etc/hosts to prevent HostNotFoundErrors
if [[ ! -z "${HOSTS}" ]]; then
  oIFS=${IFS}
  IFS=";"
  declare -a newhosts=($HOSTS)
  IFS="$oIFS"
  unset oIFS
  for i in "${newhosts[@]}"; do
    echo "$i" >> /etc/hosts
  done
fi

while poetry run /app/main.py; do sleep ${INTER_RUN_INTERVAL}; done

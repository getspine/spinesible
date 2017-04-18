#!/bin/bash
# Executes an Ansible playbook with all vault credentials, using a password file.

set -eo pipefail

if [ $# -lt 2 ]; then
  echo
  echo "Executes an Ansible playbook with all vault credentials, using a password file."
  echo "Usage: ./v DC [args]"
  exit -1
fi

DIR=$(git rev-parse --show-toplevel)

source ${DIR}/utils/spinedc
source ${DIR}/env/bin/activate

ansible-playbook --vault-password-file ~/.vault -e @vault/creds.yml -u ansibler -i ./inventory/ec2 "${@}"

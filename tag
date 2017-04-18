#!/bin/bash
# Tags an Ansible group with the provided EC2 tag.

set -eo pipefail

if [ $# -lt 4 ]; then
  echo
  echo "Tags the provided Ansible group with an EC2 tag."
  echo "Usage: ./tag DC ANSIBLE_GROUP KEY VALUE"
  exit -1
fi

DIR=$(git rev-parse --show-toplevel)

source ${DIR}/utils/spinedc

export ANSIBLE_GROUP="${1}"
shift
if [ "${GROUP}" != "all" ]; then
  export ANSIBLE_GROUP="tag_ansible_group_${ANSIBLE_GROUP}"
fi

export KEY="${1}"
export VALUE="${2}"
export SHOULD_DELETE="no"

ansible-playbook --vault-password-file ~/.vault -e @vault/creds.yml -u ansibler -i ./inventory/ec2 tag.yml

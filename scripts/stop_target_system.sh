#!/bin/bash
DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd ${DATA_DIR}/mps-node
source load_env.sh

echo "checking for extra nodes..."
if [ -f "${DATA_DIR}/${EXTRANODE_JSON_CONFIG_FILENAME}" ]; then
    echo "${DATA_DIR}/${EXTRANODE_JSON_CONFIG_FILENAME} exists. Will stop extra node"
    cd ${DIR}/../ansible-files/
    ansible-playbook -i inventory.ini target-system.yml -e "@${DATA_DIR}/${EXTRANODE_JSON_CONFIG_FILENAME}" -e gitlab_user=${GITLAB_USER} -e gitlab_pass=${GITLAB_PASS} -l extra --tags "stop"
    cd ${DATA_DIR}/mps-node
else
    echo "${DATA_DIR}/${EXTRANODE_JSON_CONFIG_FILENAME} does not exists."
fi
./compose-all.sh -f ${TARGET_COMPOSE_OVERRIDE_FILENAME} down
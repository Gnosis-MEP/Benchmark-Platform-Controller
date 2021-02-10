#!/bin/bash
DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$USE_GPU" == "1" ]
then
    echo "USING GPU!"
    COMPOSE_SCRIPT=compose-all.sh
else
    COMPOSE_SCRIPT=compose-media.sh
fi

cd ${DATA_DIR}/mps-node
source load_env.sh

./${COMPOSE_SCRIPT} -f ${TARGET_COMPOSE_OVERRIDE_FILENAME} pull
./${COMPOSE_SCRIPT} -f ${TARGET_COMPOSE_OVERRIDE_FILENAME} up -d

sleep 1
echo "checking for extra nodes..."
if [ -f "${DATA_DIR}/${EXTRANODE_JSON_CONFIG_FILENAME}" ]; then
    echo "${DATA_DIR}/${EXTRANODE_JSON_CONFIG_FILENAME} exists. Will setup and start extra node"
else
    echo "${DATA_DIR}/${EXTRANODE_JSON_CONFIG_FILENAME} does not exists."
fi


# docker-compose -f docker-compose.yml -f docker-compose-with-gpu-obj-detection.yml -f ${TARGET_COMPOSE_OVERRIDE_FILENAME} pull

# docker-compose -f docker-compose.yml -f docker-compose-with-gpu-obj-detection.yml -f ${TARGET_COMPOSE_OVERRIDE_FILENAME} up -d
sleep ${SLEEP_AFTER_TARGET_STARTUP}
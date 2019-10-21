#!/bin/bash
DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$USE_GPU" == "1" ]
then
    COMPOSE_SCRIPT=compose-all.sh
else
    COMPOSE_SCRIPT=compose-media.sh
fi

cd ${DATA_DIR}/mps-node
source load_env.sh

./${COMPOSE_SCRIPT} -f ${TARGET_COMPOSE_OVERRIDE_FILENAME} pull
./${COMPOSE_SCRIPT} -f ${TARGET_COMPOSE_OVERRIDE_FILENAME} up -d

# docker-compose -f docker-compose.yml -f docker-compose-with-gpu-obj-detection.yml -f ${TARGET_COMPOSE_OVERRIDE_FILENAME} pull

# docker-compose -f docker-compose.yml -f docker-compose-with-gpu-obj-detection.yml -f ${TARGET_COMPOSE_OVERRIDE_FILENAME} up -d
sleep ${SLEEP_AFTER_TARGET_STARTUP}
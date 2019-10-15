#!/bin/bash
DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd ${DATA_DIR}/mps-node
source load_env.sh

./compose-all.sh -f ${TARGET_COMPOSE_OVERRIDE_FILENAME} down
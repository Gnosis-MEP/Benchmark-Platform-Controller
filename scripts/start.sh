#!/bin/bash
DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

RESULT_WEBHOOK_URL=$1
echo $RESULT_WEBHOOK_URL

### prepare local env
mkdir ${DATA_DIR}
cd ${DATA_DIR}
git clone https://${GITLAB_USER}:${GITLAB_PASS}@gitlab.insight-centre.org/SIT/mps/mps-node.git
cp mps-node/example.env mps-node/.env
cp ${DATA_DIR}/${TARGET_COMPOSE_OVERRIDE_FILENAME} mps-node/${TARGET_COMPOSE_OVERRIDE_FILENAME}

git clone git@gitlab.insight-centre.org:SIT/mps/benchmark-tools.git
echo "TARGET_SYSTEM_JSON_CONFIG_PATH=${TARGET_SYSTEM_JSON_CONFIG_PATH}" >> benchmark-tools/.env
echo "BENCHMARK_JSON_CONFIG_PATH=${BENCHMARK_JSON_CONFIG_PATH}" >> benchmark-tools/.env
echo "RESULT_WEBHOOK_URL=${RESULT_WEBHOOK_URL}" >> benchmark-tools/.env

### start target system
${DIR}/start_target_system.sh

## start benchmark system
${DIR}/start_benchmark_system.sh

# ${DIR}/tag_image_latest_and_push.sh


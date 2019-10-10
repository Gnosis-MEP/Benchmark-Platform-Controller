#!/bin/bash
DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

RESULT_ID=$1
echo $RESULT_ID

### prepare local env
mkdir -p ${DATA_DIR}

cd ${DATA_DIR}
git clone https://${GITLAB_USER}:${GITLAB_PASS}@gitlab.insight-centre.org/SIT/mps/mps-node.git
cp mps-node/example.env mps-node/.env
cp ${DATA_DIR}/${TARGET_COMPOSE_OVERRIDE_FILENAME} mps-node/${TARGET_COMPOSE_OVERRIDE_FILENAME}

git clone https://${GITLAB_USER}:${GITLAB_PASS}@gitlab.insight-centre.org/SIT/mps/benchmark-tools.git
cp ${DATA_DIR}/${TARGET_SYSTEM_JSON_CONFIG_FILENAME} benchmark-tools/${TARGET_SYSTEM_JSON_CONFIG_FILENAME}
cp ${DATA_DIR}/${BENCHMARK_JSON_CONFIG_FILENAME} benchmark-tools/${BENCHMARK_JSON_CONFIG_FILENAME}

echo "TARGET_SYSTEM_JSON_CONFIG_PATH=/tmp/${TARGET_SYSTEM_JSON_CONFIG_FILENAME}" >> benchmark-tools/.env
echo "BENCHMARK_JSON_CONFIG_PATH=/tmp/${BENCHMARK_JSON_CONFIG_FILENAME}" >> benchmark-tools/.env
echo "RESULT_WEBHOOK_URL=${WEBHOOK_BASE_URL}/${RESULT_ID}" >> benchmark-tools/.env

### start target system
${DIR}/start_target_system.sh

## start benchmark system
${DIR}/start_benchmark_system.sh

# ${DIR}/tag_image_latest_and_push.sh


#!/bin/bash
DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

RESULT_ID=$1
echo $RESULT_ID

### prepare local env
mkdir -p ${DATA_DIR}
cd ${DATA_DIR}
git clone https://${GITLAB_USER}:${GITLAB_PASS}@${TARGET_SYSTEM_DEFAULT_GIT_REPOSITORY}
cp ${DATA_DIR}/${TARGET_COMPOSE_OVERRIDE_FILENAME} mps-node/${TARGET_COMPOSE_OVERRIDE_FILENAME}
cp ${DATA_DIR}/${TARGET_SYSTEM_JSON_CONFIG_FILENAME} mps-node/${TARGET_SYSTEM_JSON_CONFIG_FILENAME}
cp mps-node/example.env mps-node/.env
python ${DIR}/setup_target_system_configs.py ${DATA_DIR}/mps-node/${TARGET_SYSTEM_JSON_CONFIG_FILENAME}
cp mps-node/example.env mps-node/.env

git clone https://${GITLAB_USER}:${GITLAB_PASS}@gitlab.insight-centre.org/SIT/mps/benchmark-tools.git
cp ${DATA_DIR}/${BENCHMARK_JSON_CONFIG_FILENAME} -f benchmark-tools/${BENCHMARK_JSON_CONFIG_FILENAME}

echo "will setup benchmark tool version..."
python ${DIR}/setup_benchmarktools_version.py ${DATA_DIR}/benchmark-tools/${BENCHMARK_JSON_CONFIG_FILENAME}
# echo "RESULT_WEBHOOK_URL=${WEBHOOK_BASE_URL}/${RESULT_ID}" >> benchmark-tools/.env
# echo "TARGET_SYSTEM_JSON_CONFIG_PATH=/service/${TARGET_SYSTEM_JSON_CONFIG_FILENAME}" >> benchmark-tools/.env
# echo "BENCHMARK_JSON_CONFIG_PATH=/service/${BENCHMARK_JSON_CONFIG_FILENAME}" >> benchmark-tools/.env

### start target system
${DIR}/start_target_system.sh

## start benchmark system
${DIR}/start_benchmark_system.sh


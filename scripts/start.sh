#!/bin/bash
DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo $DIR

### prepare local env
mkdir ${DATA_DIR}
cd ${DATA_DIR}
git clone https://${GITLAB_USER}:${GITLAB_PASS}@gitlab.insight-centre.org/SIT/mps/mps-node.git
cp mps-node/example.env mps-node/.env
cp ${DATA_DIR}/${TARGET_COMPOSE_OVERRIDE_FILENAME} mps-node/${TARGET_COMPOSE_OVERRIDE_FILENAME}
# cp mps-node/load_env.sh mps-node/load_env.sh

git clone git@gitlab.insight-centre.org:SIT/mps/benchmark-tools.git
cp benchmark-tools/example.env benchmark-tools/.env

### start target system
${DIR}/start_target_system.sh

## start benchmark system
${DIR}/start_benchmark_system.sh

# ${DIR}/tag_image_latest_and_push.sh


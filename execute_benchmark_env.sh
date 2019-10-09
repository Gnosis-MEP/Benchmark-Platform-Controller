#!/bin/bash
DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo $DIR
mkdir ${DATA_DIR}
cd ${DATA_DIR}
### prepare local env
# ${DIR}/prepare_local_env.sh
git clone https://${GITLAB_USER}:${GITLAB_PASS}@gitlab.insight-centre.org/SIT/mps/mps-node.git
cp mps-node/example.env .env
cp mps-node/load_env.sh load_env.sh
# git clone git@gitlab.insight-centre.org:SIT/mps/benchmark-tools.git


### start target system
${DIR}/start_target_system.sh

# ${DIR}/tag_image_latest_and_push.sh


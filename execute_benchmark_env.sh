#!/bin/bash
DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo $DIR
mkdir /data
cd /data
### prepare local env
${DIR}/prepare_local_env.sh

### start target system
${DIR}/start_target_system.sh

# ${DIR}/tag_image_latest_and_push.sh


### cleanup
${DIR}/stop_target_system.sh
cd /
rm -r /data
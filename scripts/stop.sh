#!/bin/bash
DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULT_ID=$1
echo $RESULT_ID

echo $DIR
cd ${DATA_DIR}
### save artefacts
${DIR}/save_artefacts.sh $RESULT_ID

# ### cleanup
${DIR}/stop_target_system.sh
${DIR}/stop_benchmark_system.sh
cd $DIR
rm -rf ${DATA_DIR}
docker container prune -f
docker volume prune -f
docker image prune -f

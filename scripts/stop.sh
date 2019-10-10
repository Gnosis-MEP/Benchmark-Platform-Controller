#!/bin/bash
DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo $DIR
cd ${DATA_DIR}

### cleanup
${DIR}/stop_target_system.sh
${DIR}/stop_benchmark_system.sh
cd $DIR
rm -fr ${DATA_DIR}
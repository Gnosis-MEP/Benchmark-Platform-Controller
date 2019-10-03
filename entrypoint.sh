#!/bin/bash
# DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# mkdir /data
# cd /data

# echo $DIR
# ### prepare local env
# ${DIR}/prepare_local_env.sh

./login_to_docker_registry.sh
./run_worker.sh &
./run_webservice.sh

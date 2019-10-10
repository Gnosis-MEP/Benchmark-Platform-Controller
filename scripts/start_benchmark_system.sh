#!/bin/bash
DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd ${DATA_DIR}/benchmark-tools
source load_env.sh

docker-compose -f docker-compose.yml pull
docker-compose -f docker-compose.yml up -d
sleep ${SLEEP_AFTER_BENCHMARK_STARTUP}
#!/bin/bash
DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd ${DATA_DIR}/benchmark-tools
source load_env.sh

docker-compose -f docker-compose.yml pull
# docker-compose -f docker-compose.yml up -d
# I don't like this hack:
(cat ${BENCHMARK_JSON_CONFIG_FILENAME} | docker-compose -f docker-compose.yml run benchmark-tools)&
sleep ${SLEEP_AFTER_BENCHMARK_STARTUP}
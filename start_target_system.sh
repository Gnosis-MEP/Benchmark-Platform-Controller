#!/bin/bash
DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source load_env.sh

docker-compose -f mps-node/docker-compose.yml up -d
sleep ${SLEEP_AFTER_TARGET_STARTUP}
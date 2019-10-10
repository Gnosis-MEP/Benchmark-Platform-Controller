#!/bin/bash
DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd ${DATA_DIR}/benchmark-tools

source load_env.sh

docker-compose -f docker-compose.yml down
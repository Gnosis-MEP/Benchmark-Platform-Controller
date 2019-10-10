#!/bin/bash
DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd ${DATA_DIR}/mps-node
source load_env.sh

docker-compose -f docker-compose.yml -f docker-compose-with-gpu-obj-detection.yml down
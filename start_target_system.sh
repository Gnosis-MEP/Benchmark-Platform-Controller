#!/bin/bash

source load_env.sh

docker-compose -f mps-node/docker-compose.yml up -d
sleep ${SLEEP_AFTER_TARGET_STARTUP}
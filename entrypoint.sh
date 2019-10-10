#!/bin/bash

./scripts/login_to_docker_registry.sh

./run_worker.sh &
./run_webservice.sh

#!/bin/bash
./scripts/login_to_docker_registry.sh

./wait-for db:5432  -- echo "db is up"
./run_worker.sh &
./run_webservice.sh

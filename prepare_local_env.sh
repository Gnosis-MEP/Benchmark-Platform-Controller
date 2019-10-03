#!/bin/bash

git clone https://${GITLAB_USER}:${GITLAB_PASS}@gitlab.insight-centre.org/SIT/mps/mps-node.git
cp mps-node/example.env .env
cp mps-node/load_env.sh load_env.sh
# git clone git@gitlab.insight-centre.org:SIT/mps/benchmark-tools.git


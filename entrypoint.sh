#!/bin/bash
DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir /data
cd /data

echo $DIR
### prepare local env
${DIR}/prepare_local_env.sh


#!/bin/bash

BASE_IMAGE=${1}
BASE_TAG=${2}
TARGET_IMAGE=${3}
TARGET_TAG=${4}

echo "output:"
echo "${BASE_IMAGE}:${BASE_TAG} ${TARGET_IMAGE}:${TARGET_TAG}"
docker tag ${BASE_IMAGE}:${BASE_TAG} ${TARGET_IMAGE}:${TARGET_TAG}
docker push ${TARGET_IMAGE}:${TARGET_TAG}
echo "done pushing ${TARGET_IMAGE}:${TARGET_TAG}"
# sleep 5
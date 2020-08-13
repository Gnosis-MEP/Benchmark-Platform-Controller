#!/bin/bash
RESULT_ID=$1

BENCHMARK_CONTAINER_NAME="benchmark-tools_benchmark-tools_run_1"
ARTEFACTS_FILE_NAME="artefacts_${RESULT_ID}.tar.gz"

cd ${DATA_DIR}
docker cp ${BENCHMARK_CONTAINER_NAME}:/service/outputs ./execution_artefacts
tar -czvf $ARTEFACTS_FILE_NAME ./execution_artefacts
cp $ARTEFACTS_FILE_NAME $ARTEFACTS_DIR/$ARTEFACTS_FILE_NAME
wget -O- --post-data="{\"artefacts\": \"${ARTEFACTS_FILE_NAME}\"}" --header='Content-Type:application/json' "http://localhost:5000/api/v1.0/set_artefacts/${RESULT_ID}"

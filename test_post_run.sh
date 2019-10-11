#!/bin/bash

# wget -T 10 -O- --post-data='{"override_services": {"query-manager": {"image": "registry.insight-centre.org/sit/mps/query-manager:dev"} }}' --header='Content-Type:application/json' 'http://localhost:5000/api/v1.0/run_benchmark'

wget -O- --post-data='{"some": "results"}' --header='Content-Type:application/json' 'http://localhost:5000/api/v1.0/set_result/9c26a083-f809-4ef7-81ae-7b3a2f4d2e72'

# wget -O- 'http://localhost:5000/api/v1.0/get_result/3054712a-d4b4-43ce-b5a0-ade38b760be5'

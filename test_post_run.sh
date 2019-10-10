#!/bin/bash

# wget -T 10 -O- --post-data='{"override_services": {"query-manager": {"image": "registry.insight-centre.org/sit/mps/query-manager:dev"} }}' --header='Content-Type:application/json' 'http://localhost:5000/api/v1.0/run_benchmark'

wget -O- --post-data='{"some": "results"}' --header='Content-Type:application/json' 'http://localhost:5000/api/v1.0/set_result/730cdf5e-b53f-47d4-89f0-3d307a1366a4'

# wget -O- 'http://localhost:5000/api/v1.0/get_result/3054712a-d4b4-43ce-b5a0-ade38b760be5'

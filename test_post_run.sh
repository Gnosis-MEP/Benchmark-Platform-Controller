#!/bin/bash

wget -T 10 -O- --post-data='{"override_services": {"namespace-mapper": {"image": "registry.insight-centre.org/sit/mps/namespace-mapper:latest"} }}' --header='Content-Type:application/json' 'http://localhost:5000/api/v1.0/run_benchmark'

# wget -O- --post-data='{"some": "results"}' --header='Content-Type:application/json' 'http://localhost:5000/api/v1.0/set_result/52c49a14-8fbf-490b-915b-e651a4243177'

# wget -O- 'http://localhost:5000/api/v1.0/get_result/3054712a-d4b4-43ce-b5a0-ade38b760be5'

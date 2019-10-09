#!/bin/bash

# wget -T 10 -O- --post-data='{"override_services": {"namespace-mapper": {"image": "registry.insight-centre.org/sit/mps/namespace-mapper:dev"} }}' --header='Content-Type:application/json' 'http://localhost:5000/api/v1.0/run_benchmark'

wget -O- --post-data='{"some": "results"}' --header='Content-Type:application/json' 'http://localhost:5000/api/v1.0/set_result/24ddb7a1-42f1-43c1-8290-9c3316c0f685'

# wget -O- 'http://localhost:5000/api/v1.0/get_result/3054712a-d4b4-43ce-b5a0-ade38b760be5'

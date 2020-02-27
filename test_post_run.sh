#!/bin/bash

wget -T 10 -O- --post-data='{"override_services": {"namespace-mapper": {"image": "registry.insight-centre.org/sit/mps/namespace-mapper:latest"} }}' --header='Content-Type:application/json' '10.2.16.176:5000/api/v1.0/run_benchmark'

# wget -O- --post-data='{"some": "results"}' --header='Content-Type:application/json' 'http://10.2.16.176:5000/api/v1.0/set_result/c35eb6e9-c0b1-43fc-ae5f-a19cf6013ab0 be'

# wget -O- 'http://localhost:5000/api/v1.0/get_result/3054712a-d4b4-43ce-b5a0-ade38b760be5'

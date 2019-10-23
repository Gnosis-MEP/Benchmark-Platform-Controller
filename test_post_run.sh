#!/bin/bash

# wget -T 10 -O- --post-data='{"override_services": {"namespace-mapper": {"image": "registry.insight-centre.org/sit/mps/namespace-mapper:latest"} }}' --header='Content-Type:application/json' 'http://vm-esx7-01.deri.ie:5000/api/v1.0/run_benchmark'

wget -O- --post-data='{"some": "results"}' --header='Content-Type:application/json' 'http://vm-esx7-01.deri.ie:5000/api/v1.0/set_result/a79d0ab3-32b2-4299-9952-e7b4872171cc'

# wget -O- 'http://localhost:5000/api/v1.0/get_result/3054712a-d4b4-43ce-b5a0-ade38b760be5'

#!/bin/bash

while [ 1 ]; do
    python test_benchmark.py http://10.2.16.176:5000 namespace-mapper registry.insight-centre.org/sit/mps/namespace-mapper latest >> output_stress_test.log 2>&1
    sleep 10
    test $? -gt 30 && break
done
# wget -T 10 -O- --post-data='{"override_services": {"namespace-mapper": {"image": "registry.insight-centre.org/sit/mps/namespace-mapper:latest"} }}' --header='Content-Type:application/json' 'http://10.2.16.255:5000/api/v1.0/run_benchmark'

# wget -O- --post-data='{"some": "results"}' --header='Content-Type:application/json' 'http://10.2.16.255:5000/api/v1.0/set_result/7df8e326-4961-4f55-b770-d25b55b60fad'

# wget -O- 'http://localhost:5000/api/v1.0/get_result/3054712a-d4b4-43ce-b5a0-ade38b760be5'



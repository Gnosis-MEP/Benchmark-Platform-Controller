#!/bin/bash

wget -T 10 -O- --post-data='{"override_services": {"namespace-mapper": {"image": "registry.insight-centre.org/sit/mps/namespace-mapper:dev"} }}' --header='Content-Type:application/json' 'http://localhost:5000/api/v1.0/run_benchmark'

# wget -O- 'http://localhost:5000/api/v1.0/get_result/ba9ca84f-a223-4bf5-a0d0-5fff3ed5f35d'
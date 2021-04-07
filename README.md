# Benchmark Platform Controller
This is system is responsible for controlling the full benchmark environment for our MPS.
It provides a web API to controll the benchmarks of the target system (our MPS node) using a specific benchmark configuration and with the capacity for overriding specific configurations from the target system.

# Dependencies
There are a few requirements necessary for running this system:

* docker
* docker-compose
* **nvidia-docker**\*
* Postgres OS Libs\*\*

**Nvidia-docker\***: Required only if using GPU. And if using the latest version of nvidia-docker, it's also necessary to install `nvidia-container-runtime` and configure `/etc/docker/daemon.json` with the `nvidia` runtime ([reference](https://github.com/NVIDIA/nvidia-docker/blob/16345fb10e8b0c7285375641ef6ee12063af584c/daemon.json)), this is necessary to maintain backward compatbility and compatiblity issues with docker-compose.

Postgres OS Libs \*\*: Only necessary if installing locally for development instead of using the docker image. Eg of library (ubuntu): `libpq-dev`

# Docker Images Access
It's necessary to login into our gitlab container registry in order to have access to the docker images.

```
docker login registry.insight-centre.org
```

# Preparing Environment variables
Copy the example.env file into a new file called `.env` and update the following variables:
## SIT_PYPI_USER, SIT_PYPI_PASS
This should match our private pypi repository's username and password.

## GITLAB_USER, GITLAB_PASS
Self explanatory, but it's adivisable to actually create and use a [PERSONAL_ACCESS_TOKEN](https://gitlab.insight-centre.org/profile/personal_access_tokens)

## WEBHOOK_BASE_URL
This set to: `http://<host>:<port>/api/v1.0/set_result` but replacing `<host>` and `<port>` with your machine's IP address and the port in which the system will be running (`5000` by default).

Eg: `http://123.456.789.10:5000/api/v1.0/set_result`

## USE_GPU
If you want the benchmark to run with GPU enabled services, you should add `USE_GPU=1` to the .env file.
Otherwise if you don't want GPU enabled services, **remove** the variable from the file.


## SLEEP_AFTER_TARGET_STARTUP, SLEEP_AFTER_BENCHMARK_STARTUP
Determines how long (seconds) the system should wait after starting up the target system and the benchmark system, respectively.
This helps ensuring that all services are fully up and running before the benchmark starts it's tasks.

# Preparing Benchmark Tools Configurations
Copy the `example-configs.json` file into a new file called `configs.json` and update it's content to represent what is the default benchmark that will be executed on each run.
The **result_webhook** variable is currently overrided for each benchmark execution, as such, changing this is not required.
More information on how to write this file should be read on the Benchmark Tools docs.

# Runnig with Docker
First **pull** all the images:
`docker-compose pull`
Then, start the containers:

If you want GPU enabled, execute the following command:
```shell
docker-compose -f docker-compose.yml -f docker-compose-gpu.yml up -d
```

# Running without Docker

## Installing Dependencies

### Using pipenv
Run `$ pipenv shell` to create a python virtualenv and load the .env into the environment variables in the shell.

Then run: `$ pipenv install` to install all packages, or `$ pipenv install -d` to also install the packages that help during development, eg: ipython.
This runs the installation using **pip** under the hood, but also handle the cross dependency issues between packages and checks the packages MD5s for security mesure.


### Using pip
To install using pip directly, one needs to use the `--extra-index-url` when running the `pip install` command, in order for to be able to use our private Pypi repository.

Load the environment variables from `.env` file using `source load_env.sh`.

To install from the `requirements.txt` file, run the following command:
```
$ pip install --extra-index-url https://${SIT_PYPI_USER}:${SIT_PYPI_PASS}@sit-pypi.herokuapp.com/simple -r requirements.txt
```
## Running locally
Have Postgres and redis running: `docker-compose up -d db tasks-redis` then.
Execute both `run_webservice.sh` and `run_worker.sh`.


Otherwise, execute:
```shell
docker-compose up -d
```
**PS**: If using docker, pay attention to the IP address used in the configurations, such that the benchmark system should be able to talk to the target system and to send the results to the `WEBHOOK_BASE_URL`.

# Workflow
All communication with the platform controller is done through the web API: `http://<host>:<port>/api/v1.0`, , but replacing `<host>` and `<port>` with your machine's IP address and the port in which the system is running (`5000` by default).
## Running a Benchmark
To run a benchmark just send a HTTP POST to the following api endpoint: `/api/v1.0/run_benchmark`.

### Payload
Example of payload:
```json
{
    "override_services": {
        "namespace-mapper": {
            "image": "registry.insight-centre.org/sit/mps/namespace-mapper:some-tag"
        },
        "forwarder": {
            "image": "registry.insight-centre.org/sit/mps/forwarder:other-tag",
            "cpus": "2.5"
        }
    },
    "target_system":{
        "version": "1.0.0"
    }
}
```
In this example, the system would start up the target system (MPS Node project) using the version "1.0.0" as a basis, but replacing the Namespace-Mapper tag with the `some-tag`. And also replacing the Forwarder docker image tag with `other-tag`, as well as changing the docker `cpus` configuration for 2.5.

If `target_system` is empty it will use the latest version from the master branch of the target system.

If `override_services` is empty, it will use the specified version as it is.

### More examples of payload

#### Running bleeding edge version of Gnosis (aka: branch master)
```json
{
    "override_services": {}
}
```

#### Using many configurations override for a service
```json
{
    "override_services": {
        "object-detection": {
            "image": "registry.insight-centre.org/sit/mps/content-extraction-service:game-demo",
            "mem_limit": "800mb",
            "environment": [
                "DNN_WEIGHTS_PATH=/content-extractor/content_extraction_service/dnn_model/yolo_coco_v3/yolo.h5"
            ]
        }
    }
}
```

#### Adding new services ontop of specific Gnosis version
```json
{
    "override_services": {
        "new-service": {
            "image": "registry.insight-centre.org/sit/mps/my-new-service:some-tag",
            "mem_limit": "800mb",
            "environment": [
                "PYTHONUNBUFFERED=0",
                "SERVICE_STREAM_KEY=whatever-data",
                "SERVICE_CMD_KEY=whatever-cmd",
                "LOGGING_LEVEL=DEBUG"
            ]
        }
    },
    "target_system":{
        "version": "v1.1.0"
    }
}
```

#### Overriding Gnosis git repository
It is possible to specify a different Gnosis git repository to be used for the benchmark (i.e: a fork of the MPS node project). It is important to remember that all the necessary Gitlab permissions must be configured for the CI user (`GITLAB_USER` and `GITLAB_PASS` configs) in this fork of the project as well. To override the Target System git repository, just provide the `['target_system']['git_repository']` in the payload, the git repository address (http address, without the `http://` part) has to be set as the following: `gitlab.insight-centre.org/SIT/mps/mps-node.git`.
```json
{
    "target_system": {
        "git_repository": "gitlab.insight-centre.org/SIT/mps/mps-node.git"
    }
}
```

#### Overriding Benchmark Tools configurations
```json
{
    "override_services": {
    },
    "target_system":{
    },
    "benchmark": {
        //... benchmark tools valid config json goes in here
    }
}
```

#### Setting specific Benchmark Tools version
It is possible to specify a given git tag/branch/commit hash for the benchmark-tools project, which will make sure that the benchmark is executed with that specific version. However, the specified version needs to be configured to use a different docker image.
```json
{
    "override_services": {
    },
    "target_system":{
    },
    "benchmark": {
        "benchmark-version": "some-git-hash/tag",
        //... rest of the benchmark tools valid config json goes in here
    }
}
```


#### Datasets Usage
This datasets need to be available in the `./datasets` directory, and the `DATASETS_PATH_ON_HOST` env var needs to be configured to the absolute path to this directory in the **HOST** machine.
```json
{
    "override_services": {
    },
    "target_system":{
    },
    "datasets": [
        "coco2017-val-300x300-30fps.flv",
        "coco2017-val-300x300-60fps.flv"
    ]
}
```
Any dataset listed in there, will be made available as a VOD (Video On Demand) at the `media-server` on the url `rtmp://<machine_ip>/vod2/<dataset-name>`. Eg: `rtmp://172.17.0.1/vod2/coco2017-val-300x300-30fps.flv`.
This configuration only makes the dataset videos available, it doesn't configure a publisher for this. To do that one needs to use a custom `benchmark` configuration with the appropriate data to use this dataset (eg: Registering a publisher that uses the VOD url for that dataset).


### Response
Sending this request should give back two possible responses:

```json
{"result_id": "<result_id>"}
```
or

```json
{"wait": "<wait-time>"}
```

If a `wait` is present, then it means that the platform is currently busy right now, already executing another benchmark, and the value of this variable is how long one should wait to ask again (just to avoid overflowing the system with multiple requests at a time)

If a `result_id` is present, this means that the benchmark has started, and the value of this variable is the ID for this execution result. This ID will be necessary in order to get the output of the execution.


## Getting the Result
With the `result_id` in hands one can make a GET request to the API endpoint: `/api/v1.0/get_result/<result_id>`, replacing `<result_id>` with the actual `result_id` that one wishes to get information about.

### Response
The response will be a json containing:
```json
{
    "status": "RUNNING|FINISHED|CLEANUP",
    "result": ...
}
```

Where the `status` indicate if the benchmark is in one of the phases: `RUNNING` , `CLEANUP` (finished, but still needs to clear up environment) or `FINISHED`.

The `result` will contain the Benchmark Tools result for this execution, but this variable will be empty while the benchmark is not completed yet (eg: if status is `RUNNING`).


## Set a result* (**DONT USE THIS**)
You probably **don't want to use this endpoint**, since only the Benchmark system should be the one to give the result of a benchmark, but for the sake of clarification this will be documented as well.

To set a result for a benchmark execution, one just need to make a HTTP POST request into this API endpoint: `/api/v1.0/set_result/<result_id>`, replacing `<result_id>` with the result id of the benchmark execution you intent to set a benchmark result for.
After the result is set, the Benchmark Platform Controller will start the process of cleaning up the execution environment, and only after this task is done is that the system will be clear to perform another benchmark.

**This endpoint is also usefull for making the Benchmark Platform Controller unstuck, if the latest execution had some problem and can't finish up by itself**

### Payload
```json
{
    "some": "result"
}
```
The payload is a `json`, and it's content represent the benchmark result.

Example of invoking the endpoint on the Benchmark Server using wget:
```shell
wget -O- --post-data='{"some": "results"}' --header='Content-Type:application/json' 'http://10.2.16.176:5000/api/v1.0/set_result/749320ef-a52d-4131-8c62-aa09497eb904'
```

**PS**: Again, you don't want to use this endpoint, only the benchmark system (Benchmark Tools) should use this endpoint to push the results back to the platform controller.



# GitLab CI Simple Script for Executing Benchmark
The `test_benchmark.py` script (in the root directory of this project) is used by the Gitlab CI to run the benchmark stage, but one can download this file and run it (Python 3.6+) in order to send benchmarks to a Benchmark Platform Controller. To do so, just execute:
```shell
python test_benchmark.py http://<host>:<port> <service_name> <docker_image> <tag>
```

Where `<host>` and `<port>` is the host and port where the Benchmark Platform Controller is running, `<service_name>` is the service name (as defined in the MPS node docker-compose.yml file), `<docker_image>` and `<tag>` is the docker image and tag that will replace the service's default one during the benchmark execution.

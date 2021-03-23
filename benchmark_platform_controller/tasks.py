import datetime
import json
import os
import subprocess
import time
from urllib import request

from flask import Flask
from celery import Celery

from benchmark_platform_controller.conf_gen import create_override_yaml_file, create_json_conf_file
from benchmark_platform_controller.conf import (
    REDIS_ADDRESS,
    REDIS_PORT,
    RUN_BENCHMARK_SCRIPT,
    STOP_BENCHMARK_SCRIPT,
    TIMEOUT_SCRIPT,
    DATA_DIR,
    TARGET_COMPOSE_OVERRIDE_FILENAME,
    TARGET_SYSTEM_JSON_CONFIG_FILENAME,
    BENCHMARK_JSON_CONFIG_FILENAME,
    DATASETS_PATH_ON_HOST,
    WEBHOOK_BASE_URL,
    DEFAULT_BENCHMARK_JSON_FILE,
    EXTRANODE_JSON_CONFIG_FILENAME,
    CLEANUP_TIMEOUT
)


flask_app = Flask(__name__)
flask_app.config.update(
    CELERY_BROKER_URL=f'redis://{REDIS_ADDRESS}:{REDIS_PORT}',
    CELERY_RESULT_BACKEND=f'redis://{REDIS_ADDRESS}:{REDIS_PORT}'
)


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


celery_app = make_celery(flask_app)


def _prepare_subprocess_arglist(base_image, base_tag, target_image, target_tag):
    return [RUN_BENCHMARK_SCRIPT, base_image, base_tag, target_image, target_tag]


def default_benchmark_confs():
    configs = {}

    with open(DEFAULT_BENCHMARK_JSON_FILE, 'r') as f:
        configs = json.load(f)
    return configs


def map_dataset_to_volume(dataset):
    host_path = f'{os.path.join(DATASETS_PATH_ON_HOST, dataset)}'
    container_path = f'{os.path.join("/var/media_files/mp4s", dataset)}'
    volume = f'{host_path}:{container_path}'
    return volume


def setup_datasets_mediaserver_volume_info(datasets_confgs, override_services):
    if len(datasets_confgs) == 0:
        return override_services

    service_name = 'media-server'
    service_override = {
        'volumes': [
            map_dataset_to_volume(dataset) for dataset in datasets_confgs
        ]
    }

    if service_name in override_services:
        if 'volumes' in override_services[service_name]:
            volumes = service_override['volumes']
            volumes.extend(override_services[service_name]['volumes'])
            override_services[service_name]['volumes'] = volumes
        else:
            override_services[service_name].update(service_override)
    else:
        override_services[service_name] = service_override
    return override_services


@celery_app.task(bind=True)
def execute_benchmark(self, execution_configurations):
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    execution_id = self.request.id
    override_services = execution_configurations.get('override_services', {})
    datasets_confgs = execution_configurations.get('datasets', [])
    override_services = setup_datasets_mediaserver_volume_info(datasets_confgs, override_services)

    target_system_confs = execution_configurations.get('target_system', {})
    extra_nodes_configs = execution_configurations.get('extra_nodes', {'jetson': {}})

    # only considering jetson for now, to make it simple
    extra_nodes_configs = extra_nodes_configs.get('jetson', {})

    sleep_after_target_startup = target_system_confs.get('sleep_after_target_startup')
    target_system_git_path = target_system_confs.get('git_repository')
    call_kwargs = {}
    new_env = os.environ.copy()
    if sleep_after_target_startup is not None:
        sleep_after_target_startup = str(int(sleep_after_target_startup))
        new_env['SLEEP_AFTER_TARGET_STARTUP'] = sleep_after_target_startup

    if target_system_git_path is not None:
        new_env['TARGET_SYSTEM_DEFAULT_GIT_REPOSITORY'] = target_system_git_path

    call_kwargs['env'] = new_env

    compose_fp = create_override_yaml_file(
        DATA_DIR, TARGET_COMPOSE_OVERRIDE_FILENAME, override_services)
    targe_system_js_confs = create_json_conf_file(DATA_DIR, TARGET_SYSTEM_JSON_CONFIG_FILENAME, target_system_confs)

    if extra_nodes_configs:
        extra_nodes_configs_js = create_json_conf_file(DATA_DIR, EXTRANODE_JSON_CONFIG_FILENAME, extra_nodes_configs)

    benchmark_confs = execution_configurations.get('benchmark', default_benchmark_confs())
    set_result_url = f"{WEBHOOK_BASE_URL}/" + str(execution_id)
    benchmark_confs['result_webhook'] = set_result_url

    benchmark_js_confs = create_json_conf_file(DATA_DIR, BENCHMARK_JSON_CONFIG_FILENAME, benchmark_confs)

    call_args = [RUN_BENCHMARK_SCRIPT, execution_id]
    c = subprocess.call(
        call_args,
        **call_kwargs
    )

    # get_result_url = set_result_url.replace('set_result', 'get_result')
    # timeout_proc = subprocess.call([TIMEOUT_SCRIPT, get_result_url, set_result_url, str(EXECUTION_TIMEOUT)])
    return c


@celery_app.task()
def stop_benchmark(result_id):
    args = [STOP_BENCHMARK_SCRIPT, result_id]
    print(args)
    c = subprocess.call(
        args
    )

    return c


def check_has_timed_out(start_time):
    total_duration = datetime.datetime.now() - start_time
    total_duration = total_duration.total_seconds()
    has_timed_out = total_duration > CLEANUP_TIMEOUT
    return has_timed_out

def make_request_post(url, data):

    params = json.dumps(data).encode('utf8')
    req = request.Request(url,
                          data=params, headers={'content-type': 'application/json'})
    response = request.urlopen(req)
    return response


@celery_app.task()
def check_and_mark_finished_benchmark(mark_as_finished_url_endpoint):
    BASE_URL = WEBHOOK_BASE_URL.split('/api')[0]
    final_url = BASE_URL + mark_as_finished_url_endpoint
    start_time = datetime.datetime.now()
    params = {'forced': False}
    while not check_has_timed_out(start_time):
        time.sleep(11)
        print(f'Trying to Marking execution as finished on url {final_url}')
        res = make_request_post(final_url, params)
        if res.status == 200:
            return True
        elif res.status == 202:
            status = json.loads(res.read().decode('utf8'))
            print(f'Current Status: {status}')
            print('Cleanup not finished yet, waiting before trying again or timeout.')

    params['forced'] = False
    print(f'CLEAN UP TIMEOUT! FORCING EXECUTION AS FINISHED: {final_url}')
    res = make_request_post(final_url, params)
    return False

import json
import os
import subprocess

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
    WEBHOOK_BASE_URL,
    DEFAULT_BENCHMARK_JSON_FILE,
    EXECUTION_TIMEOUT
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


@celery_app.task(bind=True)
def execute_benchmark(self, execution_configurations):
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    execution_id = self.request.id
    override_services = execution_configurations.get('override_services', {})

    target_system_confs = execution_configurations.get('target_system', {})
    compose_fp = create_override_yaml_file(
        DATA_DIR, TARGET_COMPOSE_OVERRIDE_FILENAME, override_services)
    targe_system_js_confs = create_json_conf_file(DATA_DIR, TARGET_SYSTEM_JSON_CONFIG_FILENAME, target_system_confs)

    benchmark_confs = default_benchmark_confs()
    set_result_url = f"{WEBHOOK_BASE_URL}/" + str(execution_id)
    benchmark_confs['result_webhook'] = set_result_url

    benchmark_js_confs = create_json_conf_file(DATA_DIR, BENCHMARK_JSON_CONFIG_FILENAME, benchmark_confs)

    c = subprocess.call(
        [RUN_BENCHMARK_SCRIPT, execution_id]
    )

    # get_result_url = set_result_url.replace('set_result', 'get_result')
    # timeout_proc = subprocess.call([TIMEOUT_SCRIPT, get_result_url, set_result_url, str(EXECUTION_TIMEOUT)])
    return c


@celery_app.task()
def stop_benchmark():
    args = [STOP_BENCHMARK_SCRIPT]
    print(args)
    c = subprocess.call(
        args
    )

    return c

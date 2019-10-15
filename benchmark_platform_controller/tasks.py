import time
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
    DATA_DIR,
    TARGET_COMPOSE_OVERRIDE_FILENAME,
    TARGET_SYSTEM_JSON_CONFIG_FILENAME,
    BENCHMARK_JSON_CONFIG_FILENAME,
    WEBHOOK_BASE_URL,
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
    return {
        "benchmark": {
            "tasks": [
                {
                    "module": "benchmark_tools.task_generator.task_add_queries",
                    "args": [],
                    "kwargs": {
                        "redis_address": "172.17.0.1",
                        "redis_port": "6379",
                        "input_cmd_stream_key": "qm-cmd",
                        "logging_level": "DEBUG"
                    },
                    "actions": [
                        {
                            "action": "addQuery",
                            "query": "select object_detection from publisher 1 where (object.label = 'car') within TIMEFRAMEWINDOW(10) withconfidence >50 ",
                            "subscriber_id": "3",
                            "query_id": "1"
                        },
                        {
                            "action": "task_gen_wait_for",
                            "sleep_time": "20"
                        },
                        {
                            "action": "delQuery",
                            "subscriber_id": "3",
                            "query_id": "1"
                        },
                        {
                            "action": "task_gen_wait_for",
                            "sleep_time": "3"
                        }
                    ]
                }
            ]
        },
        "target_system": {
        },
        "result_webhook": f"{WEBHOOK_BASE_URL}/"
    }


@celery_app.task(bind=True)
def execute_benchmark(self, override_services):
    # repository = 'registry.insight-centre.org/sit/mps/docker-images/'

    # target_image = None
    # target_tag = 'latest'
    # base_image = None
    # base_tag = None
    # for service_name, settings in override_services.items():
    #     # non_repository_image_name = settings['image'].split('/')[-1].split(':')[0]
    #     base_image, base_tag = settings['image'].split(':')
    #     target_image = base_image
    #     target_tag = 'latest'

    #     break
    # print(base_image, base_tag, target_image, target_tag)
    # args = _prepare_subprocess_arglist(base_image, base_tag, target_image, target_tag)
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    execution_id = self.request.id


    compose_fp = create_override_yaml_file(
        DATA_DIR, TARGET_COMPOSE_OVERRIDE_FILENAME, override_services)
    targe_system_js_confs = create_json_conf_file(DATA_DIR, TARGET_SYSTEM_JSON_CONFIG_FILENAME, {})

    benchmark_confs = default_benchmark_confs()
    benchmark_confs['result_webhook'] += str(execution_id)

    benchmark_js_confs = create_json_conf_file(DATA_DIR, BENCHMARK_JSON_CONFIG_FILENAME, benchmark_confs)

    c = subprocess.call(
        [RUN_BENCHMARK_SCRIPT, execution_id]
    )
    return c


@celery_app.task()
def stop_benchmark():
    args = [STOP_BENCHMARK_SCRIPT]
    print(args)
    c = subprocess.call(
        args
    )

    return c

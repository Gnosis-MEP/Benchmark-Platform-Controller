import os
import subprocess

from flask import Flask
from celery import Celery

from benchmark_platform_controller.conf import REDIS_ADDRESS, REDIS_PORT, PROJECT_ROOT, RUN_BENCHMARK_SCRIPT


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


@celery_app.task()
def add_together(a, b):
    return a + b


def _prepare_subprocess_arglist(base_image, base_tag, target_image, target_tag):
    return [RUN_BENCHMARK_SCRIPT, base_image, base_tag, target_image, target_tag]


@celery_app.task()
def execute_benchmark(override_services):
    # repository = 'registry.insight-centre.org/sit/mps/docker-images/'
    target_image = None
    target_tag = 'latest'
    base_image = None
    base_tag = None
    for service_name, settings in override_services.items():
        # non_repository_image_name = settings['image'].split('/')[-1].split(':')[0]
        base_image, base_tag = settings['image'].split(':')
        target_image = base_image
        target_tag = 'latest'

        break
    print(base_image, base_tag, target_image, target_tag)

    args = _prepare_subprocess_arglist(base_image, base_tag, target_image, target_tag)
    print(args)
    c = subprocess.call(
        args
    )
    return c

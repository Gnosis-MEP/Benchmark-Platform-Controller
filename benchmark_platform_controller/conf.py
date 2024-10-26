import glob
import os

from decouple import config

SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SOURCE_DIR)
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, 'scripts')

DATA_DIR = config('DATA_DIR', default='/tmp/data')
ARTEFACTS_DIR = config('ARTEFACTS_DIR', default=os.path.join(SOURCE_DIR, 'artefacts'))

EXTRANODE_JSON_CONFIG_FILENAME = config('EXTRANODE_JSON_CONFIG_FILENAME', default='extra-node-confs.json')

TARGET_SYSTEM_DEFAULT_GIT_REPOSITORY = config(
    'TARGET_SYSTEM_DEFAULT_GIT_REPOSITORY', default='gitlab.insight-centre.org/SIT/mps/mps-node.git')

TARGET_COMPOSE_OVERRIDE_FILENAME = config('TARGET_COMPOSE_OVERRIDE_FILENAME', default='docker-compose-override.yml')

TARGET_SYSTEM_JSON_CONFIG_FILENAME = config('TARGET_SYSTEM_JSON_CONFIG_FILENAME', default='ts.json')
BENCHMARK_JSON_CONFIG_FILENAME = config('BENCHMARK_JSON_CONFIG_FILENAME', default='configs.json')

DEFAULT_BENCHMARK_JSON_FILE = config('DEFAULT_BENCHMARK_JSON_FILE', default='configs.json')

BENCHMARK_TEMPLATES_DIR = config('BENCHMARK_TEMPLATES_DIR', default=os.path.join(PROJECT_ROOT, 'benchmark_templates'))

REDIS_ADDRESS = config('REDIS_ADDRESS', default='localhost')
REDIS_PORT = config('REDIS_PORT', default='6379')

DATABASE_URL = config('DATABASE_URL', default='sqlite:///platform-controller.db')

RUN_BENCHMARK_SCRIPT = config(
    'RUN_BENCHMARK_SCRIPT', default=os.path.join(SCRIPTS_DIR, 'start.sh'))

STOP_BENCHMARK_SCRIPT = config(
    'STOP_BENCHMARK_SCRIPT', default=os.path.join(SCRIPTS_DIR, 'stop.sh'))

TIMEOUT_SCRIPT = config(
    'TIMEOUT_SCRIPT', default=os.path.join(SCRIPTS_DIR, 'timeout.py'))

DATASETS_PATH_ON_HOST = config('DATASETS_PATH_ON_HOST', default=os.path.join(PROJECT_ROOT, 'datasets'))

WEBHOOK_BASE_URL = config('WEBHOOK_BASE_URL', default='http://localhost:5000/api/v1.0/set_result')

EXECUTION_TIMEOUT = config('EXECUTION_TIMEOUT', default=60)

CLEANUP_TIMEOUT = config('CLEANUP_TIMEOUT', default=20, cast=int)

LOGGING_LEVEL = config('LOGGING_LEVEL', default='DEBUG')


def load_benchmark_templates_map():
    template_map = {}
    search_path = os.path.join(BENCHMARK_TEMPLATES_DIR, '*.json')
    for file_path in glob.glob(search_path):
        template_name = os.path.basename(file_path).split('.json')[0]
        template_map[template_name] = file_path
    return template_map


BENCHMARK_TEMPLATES_MAP = load_benchmark_templates_map()

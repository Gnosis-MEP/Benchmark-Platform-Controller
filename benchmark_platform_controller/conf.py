import os

from decouple import config

SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SOURCE_DIR)
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, 'scripts')

DATA_DIR = config('DATA_DIR', default='/tmp/data')
TARGET_COMPOSE_OVERRIDE_FILENAME = config('TARGET_COMPOSE_OVERRIDE_FILENAME', default='docker-compose-override.yml')

TARGET_SYSTEM_JSON_CONFIG_FILENAME = config('TARGET_SYSTEM_JSON_CONFIG_FILENAME', default='ts.json')
BENCHMARK_JSON_CONFIG_FILENAME = config('BENCHMARK_JSON_CONFIG_FILENAME', default='configs.json')

DEFAULT_BENCHMARK_JSON_FILE = config('DEFAULT_BENCHMARK_JSON_FILE', default='configs.json')

REDIS_ADDRESS = config('REDIS_ADDRESS', default='localhost')
REDIS_PORT = config('REDIS_PORT', default='6379')

DATABASE_URL = config('DATABASE_URL', default='sqlite:///platform-controller.db')

RUN_BENCHMARK_SCRIPT = config(
    'RUN_BENCHMARK_SCRIPT', default=os.path.join(SCRIPTS_DIR, 'start.sh'))

STOP_BENCHMARK_SCRIPT = config(
    'STOP_BENCHMARK_SCRIPT', default=os.path.join(SCRIPTS_DIR, 'stop.sh'))

WEBHOOK_BASE_URL = config('WEBHOOK_BASE_URL', default='http://localhost:5000/api/v1.0/set_result')

LOGGING_LEVEL = config('LOGGING_LEVEL', default='DEBUG')

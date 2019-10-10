import os

from decouple import config

SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SOURCE_DIR)
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, 'scripts')

DATA_DIR = config('DATA_DIR', default='/tmp/data')
TARGET_COMPOSE_OVERRIDE_FILENAME = config('TARGET_COMPOSE_OVERRIDE_FILENAME', default='docker-compose-override.yml')

REDIS_ADDRESS = config('REDIS_ADDRESS', default='localhost')
REDIS_PORT = config('REDIS_PORT', default='6379')

DATABASE_URL = config('DATABASE_URL', default='sqlite:///platform-controller.db')

RUN_BENCHMARK_SCRIPT = config(
    'RUN_BENCHMARK_SCRIPT', default=os.path.join(SCRIPTS_DIR, 'start.sh'))

STOP_BENCHMARK_SCRIPT = config(
    'STOP_BENCHMARK_SCRIPT', default=os.path.join(SCRIPTS_DIR, 'stop.sh'))

LOGGING_LEVEL = config('LOGGING_LEVEL', default='DEBUG')

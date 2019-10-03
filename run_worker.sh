#!/bin/bash

celery -c 1 -A benchmark_platform_controller.tasks worker
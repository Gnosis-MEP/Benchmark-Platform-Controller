#!/bin/bash

celery -c 1 -l DEBUG -A benchmark_platform_controller.tasks worker
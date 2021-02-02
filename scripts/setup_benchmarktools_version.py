#!/usr/bin/env python
import os
import json
import sys
import subprocess


def run(config_file_path):
    benchmark_tools_dir = os.path.dirname(config_file_path)
    configs = {}
    with open(config_file_path, 'r') as f:
        configs = json.load(f)
    if 'benchmark-version' in configs:
        bm_version = configs.pop('benchmark-version')
        subprocess.run(['git', 'checkout', bm_version], cwd=benchmark_tools_dir)
        with open(config_file_path, 'w') as f:
            json.dump(configs, f)


if __name__ == '__main__':
    config_file_path = sys.argv[1]
    run(config_file_path)

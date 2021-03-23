#!/usr/bin/env python
import os
import json
import sys
import subprocess


def run(config_file_path):
    target_system_dir = os.path.dirname(config_file_path)
    with open(config_file_path, 'r') as f:
        configs = json.load(f)
        if 'version' in configs.keys():
            version = configs.get('version')
            subprocess.run(['./set_node_version.sh', version], cwd=target_system_dir)


if __name__ == '__main__':
    config_file_path = sys.argv[1]
    run(config_file_path)

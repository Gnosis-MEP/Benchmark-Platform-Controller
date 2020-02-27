#!/usr/bin/env python
import time
from urllib import request
import json
import sys

STATUS_RUNNING = 'RUNNING'


def make_request_post(url, data):

    params = json.dumps(data).encode('utf8')
    req = request.Request(url,
                          data=params, headers={'content-type': 'application/json'})
    response = request.urlopen(req)
    return response


def force_result_by_timeout(set_result_webhook_url, execution_timeout):
    params = {
        'error': f'timeout_limit_exceded:{execution_timeout}'
    }
    res = make_request_post(set_result_webhook_url, params)
    if res.status == 200:
        print('Sucessfully forced result')
    else:
        content = res.read().decode('utf8')
        print('Problem forcing timeout result')
        print(content)


def check_is_running(result_webhook_url):
    print(f'Timeout is checking results on url: {result_webhook_url}')
    try:
        res = request.urlopen(result_webhook_url)
        if res.status == 200:
            content = res.read().decode('utf8')
            data = json.loads(content)
            result = data.get('result')
            status = data['status']
            if status == STATUS_RUNNING:
                return True
    except:
        pass

    return False


def timeout(get_result_webhook_url, set_result_webhook_url, execution_timeout):
    result_id = get_result_webhook_url.split('/')[-1]
    for i in range(execution_timeout):
        time.sleep(1)
        if not check_is_running:
            print(f'Execution "{result_id}" no longer running, exiting timeout')
            return
        print(f'Execution still running, and timeout was not reached yet...')
        print(f'Timeout Status: {i+1}/{execution_timeout} seconds')

    print(f'TIMEOUT REACHED! FORCING FINISHE RESULT BY TIMEOUT LIMIT')
    # force_result_by_timeout(set_result_webhook_url, execution_timeout)


if __name__ == '__main__':
    get_result_webhook_url = sys.argv[1]
    set_result_webhook_url = sys.argv[2]
    execution_timeout = int(sys.argv[3])
    timeout(get_result_webhook_url, set_result_webhook_url, execution_timeout)

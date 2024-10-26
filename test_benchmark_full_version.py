#!/usr/bin/env python
import datetime
import time
from urllib import request
import json
import sys


RECHECK_RESULT_TIME = 10
STATUS_FINISHED = 'FINISHED'

GET_RESULT_ENDPOINT = '/api/v1.0/get_result/'
SET_RESULT_ENDPOINT = '/api/v1.0/set_result/'
RUN_BENCHMARK_ENDPOINT = '/api/v1.0/run_benchmark'

TOTAL_EXECUTION_TIMEOUT_LIMIT = 60 * 5


def build_url(base, endpoint):
    return base + endpoint


def assert_evaluations_ok(result_id, result):
    evaluations = result.get('evaluations', {})
    eval_passed = evaluations.get('passed', False)
    assert eval_passed, f"Evaluations didn't pass. Evaluations: {evaluations}"
    return result


def force_result_by_timeout(base_url, result_id):
    endpoint = SET_RESULT_ENDPOINT + result_id
    url = build_url(base_url, endpoint)
    params = {
        'error': f'timeout_limit_exceded:{TOTAL_EXECUTION_TIMEOUT_LIMIT}'
    }
    res = make_request_post(url, params)
    if res.status == 200:
        print('Sucessfully forced result')
    else:
        content = res.read().decode('utf8')
        print('Problem forcing timeout result')
        print(content)


def check_has_timed_out(start_time):
    total_duration = datetime.datetime.now() - start_time
    total_duration = total_duration.total_seconds()
    print(f'Current execution time:{total_duration}/{TOTAL_EXECUTION_TIMEOUT_LIMIT}')
    has_timed_out = total_duration > TOTAL_EXECUTION_TIMEOUT_LIMIT
    return has_timed_out


def check_results(base_url, result_id, start_time):
    endpoint = GET_RESULT_ENDPOINT + result_id
    url = build_url(base_url, endpoint)
    print(f'Checking results for "{result_id}" on url: {url}')
    res = make_request_get(url)
    if res.status == 200:
        content = res.read().decode('utf8')
        data = json.loads(content)
        result = data.get('result')
        status = data['status']
        if result is not None or status == STATUS_FINISHED:
            return assert_evaluations_ok(result_id, result)
        else:
            if check_has_timed_out(start_time):
                force_result_by_timeout(base_url, result_id)
                assert False, f"Benchmark timed out, execution took more than {TOTAL_EXECUTION_TIMEOUT_LIMIT} seconds"

            print((
                f'Resuts not ready yet for "{result_id}". '
                f'Waiting {RECHECK_RESULT_TIME} seconds before checking results...'
            ))
            time.sleep(RECHECK_RESULT_TIME)
            return check_results(base_url, result_id, start_time)


def run(base_url, tag, start_time):
    run_benchmark_url = build_url(base_url, RUN_BENCHMARK_ENDPOINT)
    if tag:
        params = {'override_services': {}, 'target_system': {'version': tag}}
    else:
        params = {'override_services': {}}
    print(f'Sending requests for benchmark on url "{run_benchmark_url}" with params: {params}')

    res = make_request_post(run_benchmark_url, params)
    if res.status == 200:
        content = res.read().decode('utf8')
        data = json.loads(content)
        if 'wait' in data:
            wait_time = int(data['wait'])
            print(f'Service is busy, waiting for {wait_time} seconds before next try...')
            time.sleep(wait_time)
            return run(base_url, tag, start_time)
        else:
            result_id = data['result_id']
            print(f'Waiting {RECHECK_RESULT_TIME} seconds before checking results...')
            time.sleep(RECHECK_RESULT_TIME)
            return check_results(base_url, result_id, start_time)


def make_request_get(url):
    response = request.urlopen(url)
    return response


def make_request_post(url, data):

    params = json.dumps(data).encode('utf8')
    req = request.Request(url,
                          data=params, headers={'content-type': 'application/json'})
    response = request.urlopen(req)
    return response


def print_average_results(results):
    avgs = []
    stds = []
    for result in results:
        avg = result['evaluations']['benchmark_tools.evaluation.latency_evaluation']['latency_avg']['value']
        std = result['evaluations']['benchmark_tools.evaluation.latency_evaluation']['latency_std']['value']
        avgs.append(avg)
        stds.append(std)

    avg_avg = sum(avgs) / len(results)
    avg_std = sum(stds) / len(results)
    print("Final average of values from all benchmarks:")
    print(f"avg_avg: {avg_avg}")
    print(f"avg_std: {avg_std}")


if __name__ == '__main__':
    benchmark_platform_controller_url = sys.argv[1]
    tag = sys.argv[2]
    total_benchs = 1
    if len(sys.argv) == 4:
        total_benchs = int(sys.argv[3])

    results = []
    for i in range(total_benchs):
        start_time = datetime.datetime.now()
        result = run(benchmark_platform_controller_url, tag, start_time)
        time.sleep(5)
        results.append(result)
    print(results)
    print_average_results(results)
    exit(0)

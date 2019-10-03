#!/usr/bin/env python
from flask import Flask, request, jsonify, make_response, abort
from celery.result import AsyncResult

from benchmark_platform_controller.tasks import execute_benchmark, celery_app

app = Flask(__name__)


@app.route('/api/v1.0/get_result/<string:result_id>', methods=['get'])
def get_result(result_id):
    result = AsyncResult(id=result_id, app=celery_app)
    return make_response(jsonify({'status': result.status, 'result': result.info}), 200)


@app.route('/api/v1.0/run_benchmark', methods=['post'])
def run_benchmark():
    if not request.json:
        abort(400)

    result_id = None
    override_services = request.json.get('override_services')
    if override_services:
        result = execute_benchmark.delay(override_services)
        result_id = result.id

    return make_response(jsonify({'result_id': result_id}), 200)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

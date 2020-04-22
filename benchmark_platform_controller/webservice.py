#!/usr/bin/env python
from flask import Flask, request, jsonify, make_response, abort, url_for, render_template
from celery.result import AsyncResult

from benchmark_platform_controller.tasks import execute_benchmark, stop_benchmark, celery_app
from benchmark_platform_controller.conf import DATABASE_URL
from benchmark_platform_controller.models import ExecutionModel, db

WAIT_BEFORE_ASK_TO_RUN_AGAIN = 10

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


def is_execution_finished(execution):
    if not execution:
        return True

    result = AsyncResult(id=execution.result_id, app=celery_app)
    result_status = result.status
    shutdown = None
    shutdown_status = ''
    if execution.shutdown_id:
        shutdown = AsyncResult(id=execution.shutdown_id, app=celery_app)
        shutdown_status = shutdown.status
    finished_all_process = all([status == "SUCCESS" for status in [result_status, shutdown_status]])
    return finished_all_process


@app.route('/api/v1.0/get_result/<string:result_id>', methods=['get'])
def get_result(result_id):
    try:
        execution = db.session.query(ExecutionModel).filter_by(result_id=result_id).one()
    except Exception as e:
        abort(404)
        # raise e

    result = AsyncResult(id=result_id, app=celery_app)
    result_status = result.status
    shutdown = None
    shutdown_status = ''
    if execution.shutdown_id:
        shutdown = AsyncResult(id=execution.shutdown_id, app=celery_app)
        shutdown_status = shutdown.status
    finished_all_process = all([status == "SUCCESS" for status in [result_status, shutdown_status]])
    if finished_all_process:
        execution.status = execution.STATUS_FINISHED
    db.session.commit()
    return make_response(jsonify({'status': execution.status, 'result': execution.json_results}), 200)


@app.route('/api/v1.0/set_result/<string:result_id>', methods=['post'])
def set_result(result_id):
    if not request.json:
        abort(400)
    try:
        execution = db.session.query(ExecutionModel).filter_by(result_id=result_id).one()
    except:
        abort(404)
    shutdown_id = stop_benchmark.delay()
    bm_results = request.json
    execution.status = execution.STATUS_CLEANUP
    execution.json_results = bm_results
    execution.shutdown_id = shutdown_id.id
    db.session.commit()

    return make_response(jsonify({'status': 'ok'}), 200)


def get_clear_to_go():
    try:
        last_execution = db.session.query(ExecutionModel).order_by(ExecutionModel.id.desc()).first()
    except:
        return True
    return is_execution_finished(last_execution)


@app.route('/api/v1.0/run_benchmark', methods=['post'])
def run_benchmark():
    if not request.json:
        abort(400)

    result_id = None
    execution_configurations = request.json

    # override_services = request.json.get('override_services')
    # target_system_configs = request.json
    if not get_clear_to_go():
        return make_response(jsonify({'wait': WAIT_BEFORE_ASK_TO_RUN_AGAIN}), 200)

    result = execute_benchmark.delay(execution_configurations)
    result_id = result.id

    execution = ExecutionModel(result_id=result_id)
    db.session.add(execution)
    db.session.commit()
    print(f'inside db: {[e.id for e in db.session.query(ExecutionModel).all()]}')

    return make_response(jsonify({'result_id': result_id}), 200)


@app.route('/', methods=['get'])
def list_executions():
    try:
        bm_results = db.session.query(ExecutionModel).order_by(ExecutionModel.id.desc())
        bm_results_with_urls = []
        for result in bm_results:
            bm_results_with_urls.append(url_for('get_result', result_id=result.result_id))
        bm_results = bm_results_with_urls
    except:
        bm_results = []
    return render_template('list_benchmarks.html', bm_results=bm_results)


def database_is_empty():
    table_names = db.inspect(db.engine).get_table_names()
    is_empty = table_names == []
    print('Db is empty: {}'.format(is_empty))
    return is_empty


if __name__ == '__main__':
    # with app.app_context():
    app.app_context().push()
    if database_is_empty():
        db.drop_all()
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)

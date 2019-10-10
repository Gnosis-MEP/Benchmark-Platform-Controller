#!/usr/bin/env python
from flask import Flask, request, jsonify, make_response, abort
from celery.result import AsyncResult
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker

from benchmark_platform_controller.tasks import execute_benchmark, stop_benchmark, celery_app
from benchmark_platform_controller.conf import DATABASE_URL
from benchmark_platform_controller.models import ExecutionModel, db
# from benchmark_platform_controller.database_setup import ExecutionModel, engine

# DBSession = sessionmaker(bind=engine)
# session = DBSession()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


@app.route('/api/v1.0/get_result/<string:result_id>', methods=['get'])
def get_result(result_id):
    try:
        execution = db.session.query(ExecutionModel).filter_by(id=result_id).one()
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
        execution = db.session.query(ExecutionModel).filter_by(id=result_id).one()
    except:
        abort(404)
    shutdown_id = stop_benchmark.delay()
    bm_results = request.json
    execution.status = execution.STATUS_CLEANUP
    execution.json_results = bm_results
    execution.shutdown_id = shutdown_id.id
    db.session.commit()

    return make_response(jsonify({'status': 'ok'}), 200)


@app.route('/api/v1.0/run_benchmark', methods=['post'])
def run_benchmark():
    if not request.json:
        abort(400)

    result_id = None
    override_services = request.json.get('override_services')
    if override_services:
        result = execute_benchmark.delay(override_services)
        result_id = result.id

        execution = ExecutionModel(id=result_id)
        db.session.add(execution)
        db.session.commit()
        print(f'inside db: {[e.id for e in db.session.query(ExecutionModel).all()]}')

    return make_response(jsonify({'result_id': result_id}), 200)


if __name__ == '__main__':
    # with app.app_context():
    app.app_context().push()
    db.drop_all()
    db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)

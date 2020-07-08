#!/usr/bin/env python
import base64
import io

from celery.result import AsyncResult
from flask import Flask, request, jsonify, make_response, abort, url_for, render_template
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from sqlalchemy_utils import database_exists, create_database
import numpy as np
import pandas as pd

from benchmark_platform_controller.tasks import (
    execute_benchmark,
    stop_benchmark,
    check_and_mark_finished_benchmark,
    celery_app
)
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
    try:
        execution = db.session.query(ExecutionModel).filter_by(result_id=result_id).one()
    except:
        abort(404)

    if execution.status == execution.STATUS_FINISHED:
        abort(400)

    if execution.status != execution.STATUS_CLEANUP:
        if not request.json:
            abort(400)
        shutdown_id = stop_benchmark.delay()
        check_and_mark_finished_benchmark.delay(url_for('mark_execution_as_finished', result_id=result_id))
        bm_results = request.json
        execution.status = execution.STATUS_CLEANUP
        execution.json_results = bm_results
        execution.shutdown_id = shutdown_id.id

    # Bad BM, should forcefully set it to finished this should be done with care
    # paying attention to see if there are no missing docker containers running yet.
    else:
        execution.status = execution.STATUS_FINISHED

    db.session.commit()
    return make_response(jsonify({'status': 'ok'}), 200)


@app.route('/api/v1.0/mask_as_finished/<string:result_id>', methods=['post'])
def mark_execution_as_finished(result_id):
    if not request.json:
        abort(400)

    try:
        execution = db.session.query(ExecutionModel).filter_by(result_id=result_id).one()
    except:
        abort(404)

    if execution.status == execution.STATUS_FINISHED:
        abort(400)
    result = AsyncResult(id=result_id, app=celery_app)
    result_status = result.status
    shutdown = None
    shutdown_status = ''
    if execution.shutdown_id:
        shutdown = AsyncResult(id=execution.shutdown_id, app=celery_app)
        shutdown_status = shutdown.status

    current_status = [result_status, shutdown_status]
    finished_all_process = all([status == "SUCCESS" for status in current_status])

    forced = request.json.get('forced', False)
    status = 202
    if finished_all_process or forced:
        execution.status = execution.STATUS_FINISHED
        db.session.commit()
        status = 200
    return make_response(
        jsonify({'status': execution.status, 'processes': finished_all_process, 'forced': forced}), status)


def get_clear_to_go():
    try:
        print('last execution:')
        last_execution = db.session.query(ExecutionModel).order_by(ExecutionModel.id.desc()).first()
    except:
        print('Exception return true')
        return True
    if last_execution is None:
        return True
    execution_finished = is_execution_finished(last_execution)
    is_clear = execution_finished or last_execution.status == last_execution.STATUS_FINISHED

    if execution_finished and last_execution.status != last_execution.STATUS_FINISHED:
        last_execution.status = last_execution.STATUS_FINISHED
        db.session.commit()
    return is_clear


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


@app.route('/api/v1.0/benchmarks', methods=['get'])
def api_list_executions():
    try:
        bm_results = db.session.query(ExecutionModel).order_by(ExecutionModel.id.desc())
        bm_results_with_urls = []
        for result in bm_results:
            bm_results_with_urls.append(url_for('get_result', result_id=result.result_id))
        bm_results = bm_results_with_urls
    except:
        bm_results = []

    results = {
        'benchmarks': bm_results  # not really correct, since it should include the host...
    }
    return make_response(jsonify(results), 200)


@app.route('/', methods=['get'])
def list_executions():
    try:
        bm_results = db.session.query(ExecutionModel).order_by(ExecutionModel.id.desc())
        bm_results_with_urls = []
        for result in bm_results:
            if result.status == "FINISHED":  # checking if the benchmark run is finished or not.
                latency_eval = result.json_results['evaluations']['benchmark_tools.evaluation.latency_evaluation']
                obj = {
                    'id': result.result_id,
                    'status': result.status,
                    'latency_avg': latency_eval['latency_avg']['value'],
                    'latency_std': latency_eval['latency_std']['value'],
                    'url': url_for('get_result', result_id=result.result_id)
                }
            else:  # appending None values for currently running benchmark jobs.
                obj = {
                    'id': result.result_id,
                    'status': result.status,
                    'url': url_for('get_result', result_id=result.result_id),
                    'latency_avg': None,
                    'latency_std': None
                }

            bm_results_with_urls.append(obj)

        bm_results = bm_results_with_urls
        bm_results_df = pd.DataFrame(bm_results)  # converting dict object to dataframe to use in matplotlib
        if bm_results_df.empty:  # checking if there is any data in the benchmark db.
            # path for no preview image when there is no data in becnhmark db
            imgLatencyAvg = "/static/images/no_preview.jpg"
            imgLatencyStd = "/static/images/no_preview.jpg"
        else:
            bm_results_df = bm_results_df[::-1].reset_index(drop=True)  # reversing the dataframe
            # generating matplotlib chart for latency avg and returning the path
            imgLatencyAvg = generateGraphLatencyAvg(bm_results_df['latency_avg'])
            # generating matplotlib chart for latency std and returning the path
            imgLatencyStd = generateGraphLatencyStd(bm_results_df['latency_std'])

    except:
        bm_results = []
    # renderin the base template with requied args.
    return render_template('base.html', bm_results=bm_results, imgLatencyAvg=imgLatencyAvg, imgLatencyStd=imgLatencyStd)


# Created 2 private methods for generating matplotlib charts.
# Since, in future we might change the type of charts for latency average and latency standard deviation.
# Thats why we have cretaed 2 separate methods to exclude the dependency.

def generateGraphLatencyAvg(latency_avg):
    latency_avg_mean = [np.mean(latency_avg)]  # calculating the mean of the latency average values

    # matplotlib code
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    axis.set_title("Benchmark Evaluation : Latency Average ")
    axis.set_xlabel("Benchmark Run")
    axis.set_ylabel("Latency Average ")
    axis.yaxis.grid()  # adding horizontal grid lines
    axis.set_xticks([])  # removing the x-axis ticks
    axis.plot(latency_avg, "ro-")
    axis.axhline(y=latency_avg_mean, color='blue', linestyle="--", label="Mean")  # adding the mean line.
    axis.legend(loc="upper right")  # setting the legen position.

    # matplotlib to PNG image
    pngImg = io.BytesIO()
    FigureCanvas(fig).print_png(pngImg)

    # png image to its base64 conversion.
    pngImgB64 = "data:image/png;base64,"
    pngImgB64 += base64.b64encode(pngImg.getvalue()).decode('utf8')
    return pngImgB64


def generateGraphLatencyStd(latency_std):
    latency_std_mean = [np.mean(latency_std)]

    # matplot lib code
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)  # adding subplot region.
    axis.set_title("Benchmark Evaluation : Latency Standard Deviation ")
    axis.set_xlabel("Benchmark Run")
    axis.set_ylabel("Latency Standard Deviation ")
    axis.yaxis.grid()  # adding horizontal grid lines
    axis.set_xticks([])  # removing the x-axis ticks
    axis.plot(latency_std, "ro-")
    axis.axhline(y=latency_std_mean, color='blue', linestyle="--", label="Mean")
    axis.legend(loc="upper right")  # setting the legen position.

    # matplotlib to PNG image
    pngImg = io.BytesIO()
    FigureCanvas(fig).print_png(pngImg)

    # png image to its base64 conversion.
    pngImgB64 = "data:image/png;base64,"
    pngImgB64 += base64.b64encode(pngImg.getvalue()).decode('utf8')
    return pngImgB64


def database_is_empty():
    if not database_exists(db.engine.url):
        create_database(db.engine.url)
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

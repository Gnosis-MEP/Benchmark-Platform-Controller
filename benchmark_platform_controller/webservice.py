#!/usr/bin/env python
import base64
import io
import json
import os

from celery.result import AsyncResult
from flask import Flask, request, jsonify, make_response, abort, url_for, render_template, send_file
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from sqlalchemy_utils import database_exists, create_database
import numpy as np


from benchmark_platform_controller.analysis import latency_analysis, throughput_analysis, per_service_speed_analysis, per_benchmark_analysis, tabular_view
from benchmark_platform_controller.tasks import (
    execute_benchmark,
    stop_benchmark,
    check_and_mark_finished_benchmark,
    celery_app
)
from benchmark_platform_controller.conf import DATABASE_URL, ARTEFACTS_DIR
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
        shutdown_id = stop_benchmark.delay(result_id)
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


@app.route('/api/v1.0/set_artefacts/<string:result_id>', methods=['post'])
def set_artefacts(result_id):
    if not request.json:
        abort(400)

    try:
        execution = db.session.query(ExecutionModel).filter_by(result_id=result_id).one()
    except:
        abort(404)

    artefacts = request.json.get('artefacts')
    if artefacts is not None:
        execution.artefacts = artefacts
        db.session.commit()
    status = 200

    return make_response(
        jsonify({'status': 'ok'}), status)


@app.route('/api/v1.0/get_artefacts/<string:result_id>')
def get_artefacts(result_id):
    try:
        execution = db.session.query(ExecutionModel).filter_by(result_id=result_id).one()
    except:
        abort(404)

    if execution.artefacts is None:
        abort(404)

    artefact_path = os.path.join(ARTEFACTS_DIR, execution.artefacts)
    try:
        return send_file(
            artefact_path, attachment_filename=execution.artefacts
        )
    except Exception as e:
        print(e)
        abort(404)


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


############### end of API

def is_result_valid(result):
    if result.status != "FINISHED":  # checking if the benchmark run is finished or not.
        return False

    result_passed = result.json_results.get('evaluations', {}).get('passed', False)
    return result_passed


def clean_latency_result(json):
    if ("benchmark_tools.evaluation.latency_evaluation" in json['result']["evaluations"]):
            latency_evals = {
                'status': json['result']["evaluations"]["benchmark_tools.evaluation.latency_evaluation"]["passed"],
                'value': json['result']["evaluations"]["benchmark_tools.evaluation.latency_evaluation"]["latency_avg"]["value"]
            }
    else:
        latency_evals = {
            'status': "This evaluation does not exist for the latest iteration",
            'value': "This evaluation does not exist for the latest iteration"
        }
    return latency_evals


def clean_throughput_result(json):
    if ("benchmark_tools.evaluation.throughput_evaluation" in json['result']["evaluations"]):
        throughput_evals = {
            'status': json['result']["evaluations"]["benchmark_tools.evaluation.throughput_evaluation"]["passed"],
            'value': json['result']["evaluations"]["benchmark_tools.evaluation.throughput_evaluation"]["throughput_fps"]["value"]
        }
    else:
        throughput_evals = {
            'status': "This evaluation does not exist for the latest iteration",
            'value': "This evaluation does not exist for the latest iteration"
        }
    return throughput_evals


def clean_speed_result(json):
    if ("benchmark_tools.evaluation.per_service_speed_evaluation" in json['result']["evaluations"]):
        per_service_speed_evals = {
            'status': json['result']["evaluations"]["benchmark_tools.evaluation.per_service_speed_evaluation"]["passed"]
        }
    else:
        per_service_speed_evals = {
            'status': "This evaluation does not exist for the latest iteration"
        }
    return per_service_speed_evals


@app.route('/', methods=['get'])
def list_executions():
    try:
        bm_results = db.session.query(ExecutionModel).order_by(ExecutionModel.id.desc())
        bm_results_with_urls = []
        for result in bm_results:
            obj = {
                'id': result.result_id,
                'status': result.status,
                'url': url_for('per_benchmark_result', result_id=result.result_id),
                'validation': is_result_valid(result)
            }

            bm_results_with_urls.append(obj)

        bm_results = bm_results_with_urls
        
        first_result_id = bm_results[0]['id']
        first_result_id_json = get_result(first_result_id).json
        latency_evals = clean_latency_result(first_result_id_json)
        throughput_evals = clean_throughput_result(first_result_id_json)
        per_service_speed_evals = clean_speed_result(first_result_id_json)

    except:
        bm_results = []
    # renderin the base template with requied args.
    return render_template('index.html', bm_results=bm_results, latency_evals = latency_evals, throughput_evals = throughput_evals, per_service_speed_evals = per_service_speed_evals)

@app.route('/get_result/<string:result_id>')
def per_benchmark_result(result_id):
    obj = get_result(result_id).json
    plot_json = per_benchmark_analysis(obj)
    rows = tabular_view(obj)
    det_result = {
        'ID': result_id,
        'Benchmark_Passed': obj['result']['evaluations']['passed'],
        'Query': obj['result']["configs"]["benchmark"]["tasks"][1]["kwargs"]["actions"][0]["query"],
        'Benchmark_Running_Time': obj['result']["configs"]["benchmark"]["tasks"][1]["kwargs"]["actions"][1]["sleep_time"],
        'Latency_Evaluation_Passed': obj['result']["evaluations"]["benchmark_tools.evaluation.latency_evaluation"]["passed"],
        'Latency_Value': obj['result']["evaluations"]["benchmark_tools.evaluation.latency_evaluation"]["latency_avg"]["value"],
        'Traces': obj['result']["evaluations"]["benchmark_tools.evaluation.latency_evaluation"]["data_points"]["value"],
        'Throughput_Evaluation_Passed': obj['result']["evaluations"]["benchmark_tools.evaluation.throughput_evaluation"]["passed"],
        'Throughput_Value': obj['result']["evaluations"]["benchmark_tools.evaluation.throughput_evaluation"]["throughput_fps"]["value"],
        'Per_Service_Speed_Evaluation_Passed':  obj['result']['evaluations']["benchmark_tools.evaluation.per_service_speed_evaluation"]["passed"],
        'Geolocation': obj['result']["configs"]["benchmark"]["tasks"][0]["kwargs"]["actions"][0]["meta"]["geolocation"],
        'CCTV': obj['result']["configs"]["benchmark"]["tasks"][0]["kwargs"]["actions"][0]["meta"]["cctv"],
        'Color': obj['result']["configs"]["benchmark"]["tasks"][0]["kwargs"]["actions"][0]["meta"]["color"],
        'FPS': obj['result']["configs"]["benchmark"]["tasks"][0]["kwargs"]["actions"][0]["meta"]["fps"],
        'Resolution': obj['result']["configs"]["benchmark"]["tasks"][0]["kwargs"]["actions"][0]["meta"]["resolution"],
        'Color_Channels': obj['result']["configs"]["benchmark"]["tasks"][0]["kwargs"]["actions"][0]["meta"]["color_channels"]
    }
    return render_template('per_benchmark_result.html', results = det_result, plot_json = plot_json, rows = rows)


def filter_results_with_latency(result, evaluation_name):
    if result.status == "FINISHED":  # checking if the benchmark run is finished or not.
        evaluation_list = result.json_results.get('evaluations', {})
        if evaluation_name.lower() == 'latency':
            evaluation_full_path = 'benchmark_tools.evaluation.latency_evaluation'
            has_evaluation = evaluation_full_path in evaluation_list.keys()
            if has_evaluation:
                evaluation = evaluation_list[evaluation_full_path]
                has_error = 'error' in evaluation.keys()
                if has_error is False:
                    return True

    return False


@app.route('/analysis/latency', methods=['get', 'post'])
def benchmarks_latency_analysis():
    if request.method == 'POST':
        evaluation_name = request.form['evaluation_name']
        checked_boxes_ids = []
        for key in request.form.keys():
            if 'bm_results_' in key:
                checked_boxes_ids.append(request.form[key])
        bm_results = db.session.query(ExecutionModel).order_by(ExecutionModel.id.desc())
        bm_results = filter(lambda r: r.result_id in checked_boxes_ids, bm_results)
        results_dict = {
            result.result_id: result.json_results for result in bm_results
        }
        plot_json = latency_analysis(results_dict)
        return render_template(
            'show_analysis_bar.html', plot_json=plot_json, evaluation_name=evaluation_name)
    else:
        evaluation_name = 'latency'
        bm_valid_results = []
        try:
            bm_results = db.session.query(ExecutionModel).order_by(ExecutionModel.id.desc())
            for result in bm_results:
                if filter_results_with_latency(result, evaluation_name):
                    result_obj = {
                        'id': result.result_id
                    }
                    bm_valid_results.append(result_obj)
        except:
            pass
        return render_template(
            'latency_analysis.html', bm_results=bm_valid_results, evaluation_name=evaluation_name)


def filter_results_with_throughput(result, evaluation_name):
    if result.status == "FINISHED":  # checking if the benchmark run is finished or not.
        evaluation_list = result.json_results.get('evaluations', {})
        if evaluation_name.lower() == 'throughput':
            evaluation_full_path = 'benchmark_tools.evaluation.throughput_evaluation'
            has_evaluation = evaluation_full_path in evaluation_list.keys()
            if has_evaluation:
                evaluation = evaluation_list[evaluation_full_path]
                has_error = 'error' in evaluation.keys()
                if has_error is False:
                    return True

    return False


@app.route('/analysis/throughput', methods=['get', 'post'])
def benchmarks_throughput_analysis():
    if request.method == 'POST':
        evaluation_name = request.form['evaluation_name']
        checked_boxes_ids = []
        for key in request.form.keys():
            if 'bm_results_' in key:
                checked_boxes_ids.append(request.form[key])
        bm_results = db.session.query(ExecutionModel).order_by(ExecutionModel.id.desc())
        bm_results = filter(lambda r: r.result_id in checked_boxes_ids, bm_results)
        results_dict = {
            result.result_id: result.json_results for result in bm_results
        }
        plot_json = throughput_analysis(results_dict)
        return render_template(
            'show_analysis_bar.html', plot_json=plot_json, evaluation_name=evaluation_name)
    else:
        evaluation_name = 'throughput'
        bm_valid_results = []
        try:
            bm_results = db.session.query(ExecutionModel).order_by(ExecutionModel.id.desc())
            for result in bm_results:
                if filter_results_with_throughput(result, evaluation_name):
                    result_obj = {
                        'id': result.result_id
                    }
                    bm_valid_results.append(result_obj)
        except:
            pass
        return render_template(
            'throughput_analysis.html', bm_results=bm_valid_results, evaluation_name=evaluation_name)


def filter_results_with_per_service_speed(result, evaluation_name):
    if result.status == "FINISHED":  # checking if the benchmark run is finished or not.
        evaluation_list = result.json_results.get('evaluations', {})
        if evaluation_name.lower() == 'per_service_speed':
            evaluation_full_path = 'benchmark_tools.evaluation.per_service_speed_evaluation'
            has_evaluation = evaluation_full_path in evaluation_list.keys()
            if has_evaluation:
                evaluation = evaluation_list[evaluation_full_path]
                has_error = 'error' in evaluation.keys()
                if has_error is False:
                    return True

    return False


@app.route('/analysis/per_service_speed', methods=['get', 'post'])
def benchmarks_per_service_speed_analysis():
    if request.method == 'POST':
        evaluation_name = request.form['evaluation_name']
        checked_boxes_ids = []
        for key in request.form.keys():
            if 'bm_results_' in key:
                checked_boxes_ids.append(request.form[key])
        bm_results = db.session.query(ExecutionModel).order_by(ExecutionModel.id.desc())
        bm_results = filter(lambda r: r.result_id in checked_boxes_ids, bm_results)
        results_dict = {
            result.result_id: result.json_results for result in bm_results
        }
        plot_json = per_service_speed_analysis(results_dict)
        return render_template(
            'show_analysis_bar.html', plot_json=plot_json, evaluation_name=evaluation_name)
    else:
        evaluation_name = 'per_service_speed'
        bm_valid_results = []
        try:
            bm_results = db.session.query(ExecutionModel).order_by(ExecutionModel.id.desc())
            for result in bm_results:
                if filter_results_with_per_service_speed(result, evaluation_name):
                    result_obj = {
                        'id': result.result_id
                    }
                    bm_valid_results.append(result_obj)
        except:
            pass
        return render_template(
            'per_service_speed_analysis.html', bm_results=bm_valid_results, evaluation_name=evaluation_name)





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

#!/usr/bin/env python
import copy
import json
import os

from celery.result import AsyncResult
from flask import Flask, request, jsonify, make_response, abort, url_for, render_template, send_file
from sqlalchemy_utils import database_exists, create_database


from benchmark_platform_controller.analysis import (
    latency_analysis,
    throughput_analysis,
    per_service_speed_analysis
)
from benchmark_platform_controller.tasks import (
    execute_benchmark,
    stop_benchmark,
    check_and_mark_finished_benchmark,
    celery_app
)
from benchmark_platform_controller.conf import DATABASE_URL, ARTEFACTS_DIR, BENCHMARK_TEMPLATES_MAP
from benchmark_platform_controller.models import ExecutionModel, db


WAIT_BEFORE_ASK_TO_RUN_AGAIN = 10

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False  # enable this to see sql queries in the terminal
db.init_app(app)


def load_benchmark_template_from_disk(template_name):
    file_path = BENCHMARK_TEMPLATES_MAP[template_name]
    with open(file_path, 'r') as template_file:
        return json.load(template_file)


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


def get_execution_or_404(result_id):
    try:
        execution = db.session.query(ExecutionModel).filter_by(result_id=result_id).one()
    except Exception as e:
        abort(404)
    return execution


@app.route('/api/v1.0/get_result/<string:result_id>', methods=['get'])
def get_result(result_id):
    execution = get_execution_or_404(result_id)

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
    execution = get_execution_or_404(result_id)

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

    execution = get_execution_or_404(result_id)

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


def execute_benchmark_if_clear_to_go(execution_configurations):
    if not get_clear_to_go():
        return make_response(jsonify({'wait': WAIT_BEFORE_ASK_TO_RUN_AGAIN}), 200)

    result_id = None
    result = execute_benchmark.delay(copy.deepcopy(execution_configurations))
    result_id = result.id

    execution = ExecutionModel(result_id=result_id, json_payload=execution_configurations)
    db.session.add(execution)
    db.session.commit()
    # print(f'inside db: {[e.id for e in db.session.query(ExecutionModel).all()]}')

    return make_response(jsonify({'result_id': result_id}), 200)


@app.route('/api/v1.0/run_benchmark_from_template', methods=['post'])
def run_benchmark_from_template():
    if not request.json:
        abort(400)

    request_data = request.json
    template_name = request_data.get('template_name')
    if not template_name or template_name not in BENCHMARK_TEMPLATES_MAP.keys():
        abort(make_response(jsonify(message=f'Template Name "{template_name}" is invalid.'), 400))

    template_configurations = load_benchmark_template_from_disk(template_name)
    template_override = request_data.get('template_override', {})
    template_configurations.update(template_override)
    execution_configurations = template_configurations

    return execute_benchmark_if_clear_to_go(execution_configurations)


@app.route('/api/v1.0/run_benchmark', methods=['post'])
def run_benchmark():
    if not request.json:
        abort(400)

    execution_configurations = request.json

    return execute_benchmark_if_clear_to_go(execution_configurations)


@app.route('/api/v1.0/set_artefacts/<string:result_id>', methods=['post'])
def set_artefacts(result_id):
    if not request.json:
        abort(400)

    execution = get_execution_or_404(result_id)

    artefacts = request.json.get('artefacts')
    if artefacts is not None:
        execution.artefacts = artefacts
        db.session.commit()
    status = 200

    return make_response(
        jsonify({'status': 'ok'}), status)


@app.route('/api/v1.0/get_artefacts/<string:result_id>')
def get_artefacts(result_id):
    execution = get_execution_or_404(result_id)

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


# end of API

def is_result_valid(result):
    if result.status != "FINISHED":  # checking if the benchmark run is finished or not.
        return False

    result_passed = result.json_results.get('evaluations', {}).get('passed', False)
    return result_passed


def get_overall_evaluation_result_summary_or_msg(execution, evaluation_name):
    "Specific for the overall evals of latency, throughput and per service op. proc. speed"

    evaluation_full_path = f'benchmark_tools.evaluation.{evaluation_name}'
    detailed_analysis_url = url_for(
        'generic_eval_analysis', evaluation_name=evaluation_name, main_benchmark_id=execution.result_id)
    summary = {
        'status': 'This evaluation is not present on the latest execution.',
        'eval_name_clean': evaluation_name.replace('_', ' ').capitalize(),
        'detailed_analysis_url': detailed_analysis_url,
    }

    if execution.json_results is None:
        return summary
    evaluations = execution.json_results.get('evaluations', {})

    if evaluation_full_path in evaluations.keys():
        evaluation_data = evaluations.get(evaluation_full_path, {})
        summary['status'] = evaluation_data.get('passed', False)

        if 'latency_evaluation' in evaluation_full_path:
            summary['value'] = evaluation_data.get('latency_avg', {}).get('value')

        elif 'throughput_evaluation' in evaluation_full_path:
            summary['value'] = evaluation_data.get('throughput_fps', {}).get('value')

    return summary


def get_latest_execution_results_summary(bm_results):
    latest_execution_summary = {
        'latency_evaluation': {},
        'throughput_evaluation': {},
        'per_service_speed_evaluation': {},
    }
    if len(bm_results) != 0:
        lastest_execution = bm_results[0]['execution']
        latest_execution_summary.update({
            'latency_evaluation': get_overall_evaluation_result_summary_or_msg(
                lastest_execution, 'latency_evaluation'),
            'throughput_evaluation': get_overall_evaluation_result_summary_or_msg(
                lastest_execution, 'throughput_evaluation'),
            'per_service_speed_evaluation': get_overall_evaluation_result_summary_or_msg(
                lastest_execution, 'per_service_speed_evaluation'),
        })
    return latest_execution_summary


@app.route('/', methods=['get'])
def list_executions():
    bm_results = []
    try:
        bm_results = db.session.query(ExecutionModel).order_by(ExecutionModel.id.desc())
        bm_results_with_urls = []
        for result in bm_results:
            obj = {
                'id': result.result_id,
                'status': result.status,
                'url': url_for('detailed_benchmark_result', result_id=result.result_id),
                'validation': is_result_valid(result),
                'execution': result,
            }

            bm_results_with_urls.append(obj)

        bm_results = bm_results_with_urls
    except:
        pass
    latest_execution_summary = get_latest_execution_results_summary(bm_results)
    return render_template(
        'index.html', bm_results=bm_results, latest_execution_summary=latest_execution_summary
    )


def get_analysis_and_template_for_evaluation_name(selected_executions, evaluation_name):
    results_dict = {
        execution.result_id: execution.json_results for execution in selected_executions
    }
    if evaluation_name == 'latency_evaluation':
        plot_json = latency_analysis(results_dict)
        return render_template(
            'show_analysis_bar.html', plot_json=plot_json, evaluation_name=evaluation_name)
    elif evaluation_name == 'throughput_evaluation':
        plot_json = throughput_analysis(results_dict)
        return render_template(
            'show_analysis_bar.html', plot_json=plot_json, evaluation_name=evaluation_name)

    elif evaluation_name == 'per_service_speed_evaluation':
        plot_json = per_service_speed_analysis(results_dict)
        return render_template(
            'show_analysis_bar.html', plot_json=plot_json, evaluation_name=evaluation_name)


@app.route('/generic_analysis/<string:evaluation_name>', methods=['get', 'post'])
def generic_eval_analysis(evaluation_name):
    checked_benchmark_ids = []
    if request.method == 'GET':
        main_benchmark_id = request.args.get('main_benchmark_id')
        if main_benchmark_id:
            checked_benchmark_ids.append(main_benchmark_id)

        evaluation_full_path = 'benchmark_tools.evaluation.' + evaluation_name
        finished_benchmarks = db.session.query(ExecutionModel).filter(
            ExecutionModel.status == ExecutionModel.STATUS_FINISHED
        ).order_by(ExecutionModel.id.desc())
        not_checked = lambda e: e.result_id not in checked_benchmark_ids

        filtered_benchmark_ids = []
        for execution in finished_benchmarks:
            is_execution_ok = filter_finished_results_with_evaluation_without_error(
                execution, evaluation_name, evaluation_full_path)
            if is_execution_ok and not_checked(execution):
                filtered_benchmark_ids.append(execution.result_id)
        return render_template(
            'analysis/generic/select_executions.html',
            evaluation_name=evaluation_name, benchmark_ids=filtered_benchmark_ids,
            checked_benchmark_ids=checked_benchmark_ids)

    elif request.method == 'POST':
        selected_execution_ids = request.form.getlist('selected_executions')
        selected_executions = db.session.query(ExecutionModel).filter(
            ExecutionModel.result_id.in_(selected_execution_ids)
        ).all()
        return get_analysis_and_template_for_evaluation_name(selected_executions, evaluation_name)


@app.route('/execution/<string:result_id>')
def detailed_benchmark_result(result_id):
    execution = get_execution_or_404(result_id)
    json_results = execution.json_results or {}
    json_payload = execution.json_payload or {}
    return render_template(
        'execution_detail/benchmark_summary.html',
        execution=execution, json_results=json_results, json_payload=json_payload)


def filter_finished_results_with_evaluation_without_error(result, evaluation_name, evaluation_path):
    if result.status == "FINISHED":  # checking if the benchmark run is finished or not.
        evaluation_list = result.json_results.get('evaluations', {})
        has_evaluation = evaluation_path in evaluation_list.keys()
        if has_evaluation:
            evaluation = evaluation_list[evaluation_path]
            has_error = 'error' in evaluation.keys()
            if has_error is False:
                return True

    return False


@app.route('/create_benchmark_from_template', methods=['get'])
def create_benchmark_from_template():
    if request.method == 'GET':
        templates = list(BENCHMARK_TEMPLATES_MAP.keys())
        print(templates)
        return render_template(
            'new_benchmark/create_benchmark.html', templates=templates
        )


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

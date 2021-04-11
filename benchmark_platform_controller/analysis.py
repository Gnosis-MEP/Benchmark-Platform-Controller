import pandas as pd
import altair as alt


def latency_analysis(dict_of_results_json):
    x = []
    y = []
    yerr = []
    for result_id, result in dict_of_results_json.items():
        content = result['evaluations']
        evaluation = content['benchmark_tools.evaluation.latency_evaluation']
        data = pd.DataFrame(evaluation)
        metric_avg = data['latency_avg'].value
        metric_std = data['latency_std'].value
        x.append(result_id)
        y.append(metric_avg)
        yerr.append(metric_std)

    x_title = 'Benchmark ID'
    y_title = 'Latency (seconds)'
    metric_name = 'latency'

    # set up data frame
    source = pd.DataFrame({'benchmark_id': x, metric_name: y, "yerr": yerr})

    # the base chart
    base = alt.Chart(source).transform_calculate(
        ymin=f"datum.{metric_name}-datum.yerr",
        ymax=f"datum.{metric_name}+datum.yerr"
    ).properties(width=300)

    # generate the bars
    bars = base.mark_bar(
        # size=30,
    ).encode(
        x=alt.X('benchmark_id:O', title=x_title),
        y=alt.Y(f'{metric_name}:Q', title=y_title),
        color=alt.Color('benchmark_id:O', title=x_title),
    )

    # generate the error bars
    errorbars = base.mark_errorbar().encode(
        x=alt.X('benchmark_id:O', title=x_title),
        y=alt.Y('ymin:Q', title=y_title),
        y2=alt.Y2('ymax:Q', title=y_title)
    )

    chart = bars + errorbars

    return chart.to_json()


def throughput_analysis(dict_of_results_json):
    x = []
    y = []
    for result_id, result in dict_of_results_json.items():
        content = result['evaluations']
        evaluation = content['benchmark_tools.evaluation.throughput_evaluation']
        data = pd.DataFrame(evaluation)
        metric_avg = data['throughput_fps'].value
        x.append(result_id)
        y.append(metric_avg)

    x_title = 'Benchmark ID'
    y_title = 'Throughput (fps)'
    metric_name = 'throughput'

    # set up data frame
    source = pd.DataFrame({'benchmark_id': x, metric_name: y})

    # generate the bars
    chart = alt.Chart(source).mark_bar(
        # size=30,
    ).encode(
        x=alt.X('benchmark_id:O', title=x_title),
        y=alt.Y(f'{metric_name}:Q', title=y_title),
        color=alt.Color('benchmark_id:O', title=x_title),
    ).properties(width=300)
    
    return chart.to_json()
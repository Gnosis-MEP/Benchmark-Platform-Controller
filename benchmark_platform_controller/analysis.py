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
    # set up data frame
    source = pd.DataFrame({'benchmark_id': x, 'latency': y, "yerr": yerr})

    # the base chart
    base = alt.Chart(source).transform_calculate(
        ymin="datum.y-datum.yerr",
        ymax="datum.y+datum.yerr"
    )

    # generate the bars
    bars = base.mark_bar(
        size=30,
    ).encode(
        x=alt.X('benchmark_id:O', title=x_title),
        y=alt.Y('latency:Q', title=y_title)
    ).interactive()

    # generate the error bars
    errorbars = base.mark_errorbar().encode(
        x=alt.X('benchmark_id:O', title=x_title),
        y="ymin:Q",
        y2="ymax:Q"
    ).interactive()

    chart = bars + errorbars

    return chart.to_json()

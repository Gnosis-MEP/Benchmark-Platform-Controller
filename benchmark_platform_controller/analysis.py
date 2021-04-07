import pandas as pd
import numpy as np
import json
import altair as alt
from vega_datasets import data

# json-results-1 file
data_1 = pd.read_json('json_files/results-1.json')
content_1 = data_1['evaluations']
main_result_1 = content_1['passed']
details_1 = content_1['benchmark_tools.evaluation.latency_evaluation']
data_1 = pd.DataFrame(details_1)
latency_1 = data_1['latency_avg'].value
std_1 = data_1['latency_std'].value

# json-results-2 file
data_2 = pd.read_json('json_files/results-2.json')
content_2 = data_2['evaluations']
main_result_2 = content_2['passed']
details_2 = content_2['benchmark_tools.evaluation.latency_evaluation']
data_2 = pd.DataFrame(details_2)
latency_2 = data_2['latency_avg'].value
std_2 = data_2['latency_std'].value

# json-results-3 file
data_3 = pd.read_json('json_files/results-3.json')
content_3 = data_3['evaluations']
main_result_3 = content_3['passed']
details_3 = content_3['benchmark_tools.evaluation.latency_evaluation']
data_3 = pd.DataFrame(details_3)
latency_3 = data_3['latency_avg'].value
std_3 = data_3['latency_std'].value

# json-results-4 file
data_4 = pd.read_json('json_files/results-4.json')
content_4 = data_4['evaluations']
main_result_4 = content_4['passed']
details_4 = content_4['benchmark_tools.evaluation.latency_evaluation']
data_4 = pd.DataFrame(details_4)
latency_4 = data_4['latency_avg'].value
std_4 = data_4['latency_std'].value

# json-results-5 file
data_5 = pd.read_json('json_files/results-5.json')
content_5 = data_5['evaluations']
main_result_5 = content_5['passed']
details_5 = content_5['benchmark_tools.evaluation.latency_evaluation']
data_5 = pd.DataFrame(details_5)
latency_5 = data_5['latency_avg'].value
std_5 = data_5['latency_std'].value

x = [1, 2, 4, 5]
y = [latency_1, latency_2, latency_4, latency_5]
yerr = [std_1, std_2, std_4, std_5]
# set up data frame
source = pd.DataFrame({"Benchmark Iteration":x, "y":y, "yerr":yerr})

# the base chart
base = alt.Chart(source).transform_calculate(
    Latency_sec="datum.y-datum.yerr",
    ymax="datum.y+datum.yerr"
)

# generate the points
points = base.mark_bar(
    size=30,
).encode(
    x=alt.X('Benchmark Iteration', scale=alt.Scale(domain=[1, 8], type ='ordinal')),
    y=alt.Y('y')
).interactive()

# generate the error bars
errorbars = base.mark_errorbar().encode(
    x=alt.X('Benchmark Iteration', scale=alt.Scale(domain=[1,8], type ='ordinal')),
    y="Latency_sec:Q",
    y2="ymax:Q"
).interactive()

chart = points + errorbars

chart.save('chart_json/all_latency.json')
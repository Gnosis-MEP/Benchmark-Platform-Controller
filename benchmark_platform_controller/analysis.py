import pandas as pd
import altair as alt
import json


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

def per_service_speed_analysis(dict_of_results_json):
    aa = []
    ap = []
    cm = []
    qm = []
    og = []
    m = []
    am = []
    f = []
    ed = []
    pp = []
    wm = []
    s = []
    ak = []
    pr = []
    qp = []
    nm = []
    std = []
    avg = []
    y = []
    y_title = 'Benchmark ID'
    x_title = 'Per Service Speed'
    metric_name = 'per_service_speed'

    for result_id, result in dict_of_results_json.items():
        content = result['evaluations']
        evaluation = content['benchmark_tools.evaluation.per_service_speed_evaluation']
        df = pd.DataFrame(evaluation)
        column_names = df.columns.tolist()
        y.append(result_id)

        for i in range(len(column_names)):
            if("AdaptationAnalyser" in column_names[i]):
                aa.append(df.iloc[:,i])

            elif("AdaptationPlanner" in column_names[i]):
                ap.append(df.iloc[:,i])

            elif("ClientManager" in column_names[i]):
                cm.append(df.iloc[:,i])

            elif("QueryManager" in column_names[i]):
                qm.append(df.iloc[:,i])

            elif("OutputGenerator" in column_names[i]):
                og.append(df.iloc[:,i])

            elif("Matcher" in column_names[i]):
                m.append(df.iloc[:,i])

            elif("AdaptationMonitor" in column_names[i]):
                am.append(df.iloc[:,i])

            elif("Forwarder" in column_names[i]):
                f.append(df.iloc[:,i])

            elif("EventDispatcher" in column_names[i]):
                ed.append(df.iloc[:,i])

            elif("PPEDetectionService" in column_names[i]):
                pp.append(df.iloc[:,i])

            elif("WindowManager" in column_names[i]):
                wm.append(df.iloc[:,i])

            elif("Scheduler" in column_names[i]):
                s.append(df.iloc[:,i])

            elif("AdaptationKnowledge" in column_names[i]):
                ak.append(df.iloc[:,i])

            elif("PreProcessing" in column_names[i]):
                pr.append(df.iloc[:,i])

            elif("QueryPlanner" in column_names[i]):
                qp.append(df.iloc[:,i])

            elif("NamespaceMapper" in column_names[i]):
                nm.append(df.iloc[:,i])

    df_AdaptationAnalyser = pd.DataFrame(aa)
    df_AdaptationPlanner = pd.DataFrame(ap)
    df_ClientManager = pd.DataFrame(cm)
    df_QueryManager = pd.DataFrame(qm)
    df_OutputGenerator = pd.DataFrame(og)
    df_Matcher = pd.DataFrame(m)
    df_AdaptationMonitor = pd.DataFrame(am)
    df_Forwarder = pd.DataFrame(f)
    df_EventDispatcher = pd.DataFrame(ed)
    df_PPEDetectionService = pd.DataFrame(pp)
    df_WindowManager = pd.DataFrame(wm)
    df_Scheduler = pd.DataFrame(s)
    df_AdaptationKnowledge = pd.DataFrame(ak)
    df_Preprocessing = pd.DataFrame(pr)
    df_QueryPlanner = pd.DataFrame(qp)
    df_NamespaceMapper = pd.DataFrame(nm)
    df_final = pd.concat([df_AdaptationAnalyser, df_AdaptationPlanner, df_ClientManager, df_QueryManager, df_OutputGenerator,
                df_Matcher, df_AdaptationMonitor, df_Forwarder, df_EventDispatcher, df_PPEDetectionService, df_WindowManager,
                df_Scheduler, df_AdaptationKnowledge, df_Preprocessing, df_QueryPlanner, df_NamespaceMapper])
    df_final = df_final["value"].to_frame()
    index = df_final.index.tolist()
    for i in range(len(index)):
        if(index[i].find('process_data_event_std')!= -1):
            std.append(df_final.iloc[i,:])

        elif(index[i].find('process_data_event_avg')!= -1):
            avg.append(df_final.iloc[i,:])
    df_std = pd.DataFrame(std)
    df_avg = pd.DataFrame(avg)
    indicator = y*(int(len(df_avg)/len(y)))
    df = pd.DataFrame({"Service":df_avg.index, metric_name:df_avg['value'], "benchmark_id": indicator})
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X(f'{metric_name}:Q', title=x_title),
        y=alt.Y('benchmark_id:O', title=y_title),
        color=alt.Color('benchmark_id:N', title=y_title),
        row=alt.Row('Service:N',header=alt.Header(labelAngle=0, labelAlign='left', labelFontSize= 15))
    ).properties(
        width=700,
        height=80
    ).interactive()

    return chart.to_json()


def per_benchmark_analysis(json_file):
    json_results = json_file['evaluations']['benchmark_tools.evaluation.per_service_speed_evaluation']
    df = pd.DataFrame(json_results).T
    df = df['value']
    df = df[df.index != 'passed']
    df = df[~df.index.str.contains("std")]

    source = pd.DataFrame({
    'Service': df.index,
    'Speed': df.values
    })

    chart = alt.Chart(source).mark_bar().encode(
        x='Service',
        y='Speed'
    ).interactive().properties(width = 1710)

    return chart.to_json()


def tabular_view(json_file):
    ser = []
    op = []
    ty = []
    val = []

    json_results = json_file['evaluations']['benchmark_tools.evaluation.per_service_speed_evaluation']
    df_speed = pd.DataFrame(json_results).T
    val.extend(df_speed.value)

    for k in range(len(df_speed)):
        txt = df_speed.index[k]
        a = txt.split("_")
        x = " ".join(a[1:-1])
        ser.append(a[0])
        op.append(x)
        ty.append(a[-1])

    json_results = json_file['evaluations']['benchmark_tools.evaluation.latency_evaluation']
    df_latency = pd.DataFrame(json_results).T
    val.extend(df_latency.value)

    for k in range(len(df_latency)):
        txt = df_latency.index[k]
        a = txt.split("_")
        x = " ".join(a[1:-1])
        ser.append(a[0])
        op.append(x)
        ty.append(a[-1])

    json_results = json_file['evaluations']['benchmark_tools.evaluation.throughput_evaluation']
    df_tp = pd.DataFrame(json_results).T
    val.extend(df_tp.value)

    for k in range(len(df_tp)):
        txt = df_tp.index[k]
        a = txt.split("_")
        x = " ".join(a[1:-1])
        ser.append(a[0])
        op.append(x)
        ty.append(a[-1])

    df = pd.DataFrame({'Service': ser, 'Operation': op, 'Type': ty, 'Value': val})
    df = df[df.Type != 'std']
    df = df[df.Service != 'passed']
    df = df[df.Service != 'data']

    row_data=list(df.values.tolist())

    return row_data


def evaluate_result(result_id, result):
    evaluations = {
        'latency_avg': lambda x: x < 1
    }

    bm_results = result.get('results', {})
    passed = True
    failed = {}
    for metric, func in evaluations.items():
        res_val = bm_results.get(metric)
        try:
            eval_result = func(res_val)
        except:
            eval_result = False
        if eval_result is False:
            failed[metric] = res_val
            passed = False
    result.update({
        'evaluation': {
            'passed': passed,
            'failed': failed
        }
    })
    return result

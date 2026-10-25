"""Reanalyze archived runs; primary logs only, historical tables untouched."""
import argparse,csv,gzip,json,math,statistics
from pathlib import Path
from metrics import parse_run
ROOT=Path(__file__).resolve().parents[1]
def write_csv(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def pareto(rows,x,y):
    return [r for r in rows if not any(s[x]<=r[x] and s[y]<=r[y] and (s[x]<r[x] or s[y]<r[y]) for s in rows)]
def analyze(output):
    output.mkdir(parents=True,exist_ok=True);runs=[]
    for p in sorted((ROOT/'data/archive').glob('*.jsonl.gz')):
        with gzip.open(p,'rt') as stream:
            for line in stream:
                record=json.loads(line)
                runs.append(dict(benchmark=p.name.split('.')[0],config=record['config'],collector=record['config'].split('-')[0],
                    **parse_run(record['files'].get('output.txt',''),record['files'].get('gc.log',''),p.name.split('.')[0])))
    if len(runs)!=616:raise ValueError('Expected 22 workloads x 28 configurations')
    groups={}
    for r in runs:groups.setdefault(r['config'],[]).append(r)
    passed_sets=[{r['benchmark'] for r in rows if r['status']=='passed'} for rows in groups.values()]
    common=set.intersection(*passed_sets);baseline={r['benchmark']:r for r in runs if r['config']=='parallel-4g-t4' and r['status']=='passed'}
    summary=[]
    for config,rows in sorted(groups.items()):
        valid=[r for r in rows if r['benchmark'] in common and r['status']=='passed']
        summary.append(dict(config=config,collector=config.split('-')[0],benchmarks=len(valid),
            geometric_runtime_ratio=math.exp(statistics.mean(math.log(r['final_iteration_ms']/baseline[r['benchmark']]['final_iteration_ms']) for r in valid)),
            mean_final_iteration_ms=statistics.mean(r['final_iteration_ms'] for r in valid),
            mean_logged_pause_fraction_pct=statistics.mean(r['logged_pause_fraction_pct'] for r in valid),
            mean_run_pause_p99_ms=statistics.mean(r['pause_p99_ms'] for r in valid if r['pause_p99_ms'] is not None)))
    write_csv(output/'runs.csv',runs);write_csv(output/'configurations.csv',summary)
    front=pareto(summary,'geometric_runtime_ratio','mean_run_pause_p99_ms');write_csv(output/'pareto.csv',front)
    result=dict(scope='Archived primary gc.log files; whole-JVM pause scope, final-iteration runtime scope',
        primary_runs=len(runs),passed=sum(r['status']=='passed' for r in runs),common_benchmarks=sorted(common),configurations=summary,
        unconfirmed_benchmarks=sorted({r['benchmark'] for r in runs if r['status']!='passed'}))
    (output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f"Analyzed {len(runs)} primary runs; {result['passed']} PASSED markers; balanced comparison across {len(common)} workloads and {len(summary)} configurations.")
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'build');a=p.parse_args();analyze(a.output)

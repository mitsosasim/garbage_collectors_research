"""Exercise real local JVM collectors with a bounded synthetic allocation fixture."""
import argparse,json,subprocess
from pathlib import Path
from metrics import parse_run
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--java',default='java');p.add_argument('--output',type=Path,default=ROOT/'build/smoke');a=p.parse_args()
    output=a.output.resolve()
    if output.exists():raise SystemExit('Choose a fresh --output directory')
    output.mkdir(parents=True);results=[]
    version=subprocess.run([a.java,'-version'],capture_output=True,text=True,check=True)
    for gc in ['ParallelGC','G1GC','ZGC']:
        log=output/(gc+'.gc.log')
        cmd=[a.java,'-XX:+Use'+gc,'-Xms64m','-Xmx64m','-XX:ParallelGCThreads=2',f'-Xlog:gc*:file={log}:uptime,level,tags:filecount=0',str(ROOT/'examples/GCProbe.java')]
        run=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
        (output/(gc+'.output.txt')).write_text(run.stdout+run.stderr)
        if run.returncode or 'GC_PROBE_COMPLETED' not in run.stdout:raise RuntimeError(gc+' did not complete: '+run.stderr)
        metrics=parse_run(run.stdout,log.read_text())
        if not metrics['pause_events']:raise RuntimeError(gc+' produced no parsed pause events')
        results.append(dict(collector=gc,command=cmd,metrics=metrics))
        print(gc,'fixture completed,',metrics['pause_events'],'pause events parsed',flush=True)
    (output/'summary.json').write_text(json.dumps(dict(scope='Synthetic fixture; not DaCapo or research performance evidence',java_version=version.stdout+version.stderr,runs=results),indent=2)+'\n')
if __name__=='__main__':main()

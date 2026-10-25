"""Plan or execute selected DaCapo runs in a new results directory."""
import argparse,json,re,shutil,subprocess,time
from pathlib import Path
import yaml
from metrics import parse_run
ROOT=Path(__file__).resolve().parents[1]
def flags(config):
    f=['-XX:+Use'+config['gc'],'-Xms'+config['xmx'],'-Xmx'+config['xmx']]
    for field,option in [('pause','MaxGCPauseMillis'),('pgc','ParallelGCThreads'),('cgc','ConcGCThreads'),('survivorRatio','SurvivorRatio'),('maxTenuringThreshold','MaxTenuringThreshold')]:
        if field in config:f.append(f'-XX:{option}={config[field]}')
    for field,option in [('pretouch','AlwaysPreTouch'),('largePages','UseLargePages')]:
        if config.get(field):f.append('-XX:+'+option)
    return f

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--list',action='store_true');p.add_argument('--config',action='append');p.add_argument('--benchmark',action='append')
    p.add_argument('--jar',type=Path);p.add_argument('--java',default='java');p.add_argument('--output',type=Path,default=ROOT/'build/new-runs')
    p.add_argument('--iterations',type=int,default=10);p.add_argument('--timeout',type=int,default=1800);p.add_argument('--execute',action='store_true')
    a=p.parse_args();configs=yaml.safe_load((ROOT/'configs.yaml').read_text())
    if a.list:
        for c in configs:print(c['name'],' '.join(flags(c)))
        return
    if not a.config or not a.benchmark or not a.jar:p.error('Specify --config, --benchmark, and --jar; add --execute to run rather than print the plan')
    known={c['name']:c for c in configs}
    if any(name not in known for name in a.config):p.error('Unknown configuration')
    if a.iterations<1 or a.timeout<1:p.error('Iterations and timeout must be positive')
    if any(not re.fullmatch(r'[a-zA-Z0-9_-]+',b) for b in a.benchmark):p.error('Invalid benchmark name')
    plans=[];output=a.output.resolve();jar=a.jar.resolve()
    for benchmark in dict.fromkeys(a.benchmark):
        for name in dict.fromkeys(a.config):
            folder=output/benchmark/name
            cmd=[a.java,*flags(known[name]),'-Duser.language=en','-Duser.country=US',f'-Xlog:gc*:file={folder}/gc.log:time,uptime,level,tags:filecount=0', '-jar',str(jar),'-n',str(a.iterations),benchmark]
            plans.append(dict(benchmark=benchmark,config=name,command=cmd))
    if not a.execute:
        print(json.dumps(plans,indent=2));return
    if not jar.is_file():p.error('DaCapo JAR not found')
    if output.exists():p.error('Output directory already exists; choose a fresh --output')
    version=subprocess.run([a.java,'-version'],capture_output=True,text=True,check=True)
    output.mkdir(parents=True)
    manifest=dict(java_version=version.stdout+version.stderr,jar=str(jar),iterations=a.iterations,timeout_s=a.timeout,runs=[])
    failed=False
    for plan in plans:
        folder=output/plan['benchmark']/plan['config'];folder.mkdir(parents=True);start=time.monotonic()
        with (folder/'output.txt').open('w') as log:
            try:
                process=subprocess.run(plan['command'],cwd=folder,stdout=log,stderr=subprocess.STDOUT,timeout=a.timeout)
                status=dict(returncode=process.returncode,timed_out=False)
            except subprocess.TimeoutExpired:status=dict(returncode=None,timed_out=True)
        metrics=parse_run((folder/'output.txt').read_text(errors='replace'),(folder/'gc.log').read_text(errors='replace') if (folder/'gc.log').exists() else '',plan['benchmark'])
        ok=status['returncode']==0 and metrics['status']=='passed';failed|=not ok
        manifest['runs'].append(dict(**plan,**status,wall_seconds=time.monotonic()-start,metrics=metrics))
        (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        print(plan['benchmark'],plan['config'],'PASSED' if ok else 'FAILED',flush=True)
    if failed:raise SystemExit(1)
if __name__=='__main__':main()

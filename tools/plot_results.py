"""Plots from corrected, explicitly scoped reanalysis of archived logs."""
import argparse,csv,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analyze import pareto
ROOT=Path(__file__).resolve().parents[1]
COLORS={'parallel':'#26718e','g1':'#c07b25','zgc':'#348268'}
def plot(summary_path,output):
    data=json.loads(summary_path.read_text());rows=data['configurations'];output.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    def save(fig,name):
        fig.suptitle('Archived JVM runs · primary logs · 20 shared workloads',fontsize=10,color='#526578',y=1.02)
        fig.savefig(output/(name+'.png'),dpi=170,bbox_inches='tight');plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,5),layout='constrained')
    for collector in COLORS:
        rs=[r for r in rows if r['collector']==collector]
        ax.scatter([r['geometric_runtime_ratio'] for r in rs],[r['mean_run_pause_p99_ms'] for r in rs],label=collector.upper(),s=65,color=COLORS[collector])
    front=sorted(pareto(rows,'geometric_runtime_ratio','mean_run_pause_p99_ms'),key=lambda r:r['geometric_runtime_ratio'])
    ax.plot([r['geometric_runtime_ratio'] for r in front],[r['mean_run_pause_p99_ms'] for r in front],':',color='#5d6770',label='Non-dominated configurations')

    ax.set(xlabel='Geometric mean final-iteration runtime / Parallel 4g, 4 threads (lower is faster)',ylabel='Mean per-run pause-event p99 [ms] (whole JVM log)',yscale='log',title='Runtime and stop-the-world pause tradeoff')
    ax.grid(alpha=.2);ax.legend();save(fig,'runtime-pauses')
    fig,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained')
    for collector in COLORS:
        rs=[r for r in rows if r['collector']==collector];x=[r['geometric_runtime_ratio'] for r in rs]
        axes[0].scatter(x,[r['mean_logged_pause_fraction_pct'] for r in rs],color=COLORS[collector],label=collector.upper(),s=60)
        axes[1].scatter([r['mean_logged_pause_fraction_pct'] for r in rs],[r['mean_run_pause_p99_ms'] for r in rs],color=COLORS[collector],label=collector.upper(),s=60)
    axes[0].set(xlabel='Normalized final-iteration runtime',ylabel='Mean logged-JVM pause fraction [%]',title='Whole-log pause fraction (includes warmups)',yscale='log')
    axes[1].set(xlabel='Mean logged-JVM pause fraction [%]',ylabel='Mean per-run pause-event p99 [ms]',title='Pause frequency/duration tradeoff',xscale='log',yscale='log')
    for ax in axes:ax.legend();ax.grid(alpha=.2)
    save(fig,'pause-fraction')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,default=ROOT/'build/summary.json');p.add_argument('--output',type=Path,default=ROOT/'build/plots');a=p.parse_args();plot(a.input,a.output)

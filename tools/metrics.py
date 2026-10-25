"""Explicitly scoped metrics for HotSpot unified logs and DaCapo output."""
import math,re
UPTIME=re.compile(r'\[(\d+(?:[.,]\d+)?)s\]')
PAUSE=re.compile(r'GC\((\d+)\) (Pause.*?)\s+(\d+(?:[.,]\d+)?)ms\s*$')
PASS=re.compile(r'===== DaCapo\s+\S+\s+(\S+) PASSED in (\d+) msec =====')
def number(text):return float(text.replace(',','.'))
def percentile(values,p):
    return sorted(values)[max(0,math.ceil(p*len(values))-1)] if values else None

def parse_run(output,gc_log,benchmark=None):
    passed=PASS.findall(output)
    if benchmark is not None:passed=[p for p in passed if p[0]==benchmark]
    status='passed' if passed else ('failed' if re.search(r'\bFAILED\b|Exception|Error:',output) else 'unconfirmed')
    events=[];seen=set();end=0.;cycle_ids=set()
    for line in gc_log.splitlines():
        times=UPTIME.findall(line)
        if times:end=max(end,number(times[-1]))
        match=PAUSE.search(line)
        if match:
            gcid,label,duration=match.groups();timestamp=times[-1] if times else ''
            event=(gcid,label,timestamp,duration)
            if event not in seen:seen.add(event);events.append(dict(gc_id=int(gcid),label=label,duration_ms=number(duration)))
        m=re.search(r'GC\((\d+)\) Garbage Collection \(',line)
        if m:cycle_ids.add(int(m[1]))
    durations=[e['duration_ms'] for e in events]
    result=dict(status=status,final_iteration_ms=int(passed[-1][1]) if passed else None,
        warmup_iterations=len(re.findall(r'completed warmup \d+ in \d+ msec',output)),
        logged_jvm_uptime_s=end,logged_pause_ms=sum(durations),pause_events=len(events),
        pause_p50_ms=percentile(durations,.50),pause_p99_ms=percentile(durations,.99),
        pause_max_ms=max(durations) if durations else None,
        logged_pause_fraction_pct=100*sum(durations)/(end*1000) if end else None,
        young_pause_events=sum(e['label'].startswith('Pause Young') for e in events),
        full_pause_events=sum(e['label'].startswith('Pause Full') for e in events),
        zgc_cycle_records=len(cycle_ids))
    return result

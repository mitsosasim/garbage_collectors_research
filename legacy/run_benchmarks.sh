#csd4845 Dimitris Asimakopoulos - hy446 project
#script to run the DaCapo benchmarks with different GC configurations from the configs.yaml file

#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

ROOT=$(pwd)
JAR="dacapo-23.11-MR2-chopin.jar"
LOGDIR="$ROOT/logs"
RESULTS="$ROOT/results/metrics1.csv"

BENCHMARKS=(
  avrora batik biojava eclipse fop graphchi h2
  jme jython kafka luindex lusearch pmd spring sunflow tomcat
  tradebeans tradesoap xalan zxing
)

mkdir -p "$LOGDIR" "$(dirname "$RESULTS")"
echo "benchmark,config,total_time_ms,total_gc_ms,pct_gc_time,min_pause_ms,p50_ms,p99_ms,max_pause_ms,young_gc_count,full_gc_count" > "$RESULTS"

for bm in "${BENCHMARKS[@]}"; do
  echo "=== Running benchmarks for: $bm ==="
  python3 - <<EOF
import yaml, subprocess, os, re, csv, statistics

ROOT = "${ROOT}"
JAR = os.path.join(ROOT, "${JAR}")
LOGDIR = os.path.join(ROOT, "logs", "${bm}")
RESULTS = "${RESULTS}"
NAME = "${bm}"

os.makedirs(LOGDIR, exist_ok=True)

with open(os.path.join(ROOT, "configs.yaml")) as f:
    configs = yaml.safe_load(f)

pass_re = re.compile(r'^===== DaCapo.* PASSED in (\d+) msec =====$')
zgc_re = re.compile(r'Collector: Garbage Collection Cycle\s+[0-9,]+\s*/\s*([0-9,]+)')
gc_time_re = re.compile(r'[)]\s*([0-9]+,[0-9]+)ms')

def parse_gc_log(path, gc_type):
    pauses = []
    young = full = 0
    with open(path) as f:
        lines = f.readlines()

    if gc_type.lower() == "zgc":
        for line in lines:
            if "System.gc()" in line:
                full += 1
            m = zgc_re.search(line)
            if m:
                val = float(m.group(1).replace(',', '.'))
                pauses.append(val)
        total_gc = sum(pauses)
        p50 = statistics.median(pauses) if pauses else 0.0
        p99 = statistics.quantiles(pauses, n=100)[98] if len(pauses) >= 100 else (max(pauses) if pauses else 0.0)
        return total_gc, [min(pauses or [0.0]), p50, p99, max(pauses or [0.0])], 0, full // 2

    else:
        for line in lines:
            if "Pause Young" in line:
                young += 1
            if "Pause Full" in line:
                full += 1
            if "Pause Young" in line or "Pause Full" in line:
                if ") " in line:
                    m = gc_time_re.search(line)
                    if m:
                        pauses.append(float(m.group(1).replace(',', '.')))
        total_gc = sum(pauses)
        pauses.sort()
        p50 = statistics.median(pauses) if pauses else 0.0
        p99 = statistics.quantiles(pauses, n=100)[98] if len(pauses) >= 100 else (max(pauses) if pauses else 0.0)
        return total_gc, [min(pauses or [0.0]), p50, p99, max(pauses or [0.0])], young // 2, full // 2

for cfg in configs:
    try:
        name = cfg['name']
        flags = [f"-XX:+Use{cfg['gc']}"]
        flags += [f"-Xms{cfg['xmx']}", f"-Xmx{cfg['xmx']}"]
        if 'pause' in cfg:
            flags.append(f"-XX:MaxGCPauseMillis={cfg['pause']}")
        if 'pgc' in cfg:
            flags.append(f"-XX:ParallelGCThreads={cfg['pgc']}")
        if 'cgc' in cfg:
            flags.append(f"-XX:ConcGCThreads={cfg['cgc']}")
        if 'survivorRatio' in cfg:
            flags.append(f"-XX:SurvivorRatio={cfg['survivorRatio']}")
        if 'maxTenuringThreshold' in cfg:
            flags.append(f"-XX:MaxTenuringThreshold={cfg['maxTenuringThreshold']}")
        if cfg.get('pretouch', False):
            flags.append("-XX:+AlwaysPreTouch")
        if cfg.get('largePages', False):
            flags.append("-XX:+UseLargePages")

        outdir = os.path.join(LOGDIR, name)
        os.makedirs(outdir, exist_ok=True)
        gc_log = os.path.join(outdir, "gc.log")
        out_txt = os.path.join(outdir, "output.txt")

        cmd = ["java"] + flags + [
            f"-Xlog:gc*:file={gc_log}:time,uptime",
            "-jar", JAR, "-n", "10", NAME
        ]
        subprocess.run(cmd, stdout=open(out_txt, "w"), stderr=subprocess.PIPE, check=True)

        total_time = None
        for line in open(out_txt):
            m = pass_re.match(line)
            if m:
                total_time = float(m.group(1))
                break
        if total_time is None:
            raise RuntimeError("Final PASSED time not found")

        total_gc, pstats, young, full = parse_gc_log(gc_log, cfg['gc'])
        pct_gc = (total_gc / total_time * 100.0) if total_time > 0 else 0.0

        row = [
            NAME, name,
            f"{total_time:.1f}", f"{total_gc:.1f}", f"{pct_gc:.2f}",
            f"{pstats[0]:.1f}", f"{pstats[1]:.1f}", f"{pstats[2]:.1f}", f"{pstats[3]:.1f}",
            young, full
        ]
        with open(RESULTS, "a") as rf:
            csv.writer(rf).writerow(row)
        print(f"[✓] {NAME} | {name}")
    except Exception as e:
        print(f"[✗] {NAME} | {cfg.get('name','<unknown>')} FAILED: {e}")
EOF
done

echo "✓ All runs complete. Metrics in $RESULTS"

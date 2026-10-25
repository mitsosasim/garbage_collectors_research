# Run and interpret the study

## Reanalyze the supplied evidence

Python 3.10+ is sufficient for archive analysis. From the repository root:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python tools/analyze.py
python tools/plot_results.py
python -m unittest discover -s tests -v
```

On Windows, create the environment with `py -3 -m venv .venv` and replace `python` above with `.\.venv\Scripts\python.exe`; activation is optional. Linux with Python 3.12 was verified. Windows was not executed here.

Open `build/plots` for figures. `build/runs.csv` has all 616 primary runs and explicit status. `build/configurations.csv` contains balanced means across the 20 shared passing workloads. `build/pareto.csv` gives non-dominated configurations for the two plotted objectives. `build/summary.json` records the workload set and scope. Use `--output PATH` for a custom analysis directory and `--input PATH/summary.json --output PATH/plots` for plotting.

## Local JVM smoke check

Install a complete JDK, including the compiler modules needed by Java source-file execution. The verified fixture used OpenJDK 17.0.20 on Linux:

```sh
python tools/smoke.py --java java --output build/my-smoke
```

Use a fresh output directory. The script starts separate Parallel GC, G1, and ZGC JVMs with a 64 MiB heap, executes `examples/GCProbe.java`, and requires a completion marker and parsed pause events. It records the Java version, commands, output, and metrics. Each process has a 60 s deadline. This is a synthetic allocation/log-parser fixture, not a latency benchmark, DaCapo workload, or replication of the historical JDK 21 measurements.

## Plan and execute DaCapo runs

The original study's logs identify **DaCapo 23.11-MR2 Chopin**, **OpenJDK 21.0.7**, eight available processors, and about 15,927 MiB reported host memory. ZGC identifies legacy single-generation mode. The original report and presentation additionally identify Ubuntu 20.04 and an Intel i7-3820 at 3.60 GHz; see the [source guide](RESEARCH.md#experiment-context). The current machine is not presented as the original benchmark host.

Obtain the matching suite JAR separately from the [official DaCapo project](https://github.com/dacapobench/dacapobench). It is not bundled. Reproduction should record the exact JDK build, JAR checksum, host configuration, and invocation. Other JDK versions can change collector modes, supported flags, and log formats.

List the configured JVM flags:

```sh
python tools/run_benchmarks.py --list
```

Print a selected run plan without launching Java:

```sh
python tools/run_benchmarks.py --jar /path/to/dacapo-23.11-MR2-chopin.jar \
  --benchmark avrora --config parallel-4g-t4 --output build/avrora-trial
```

Add `--execute` to run that exact plan. Repeat `--benchmark` or `--config` to select several. The default is ten DaCapo iterations and a 1,800 s timeout per JVM. `--iterations` and `--timeout` change those values. Each output root must be new, protecting earlier results from overwrite or log rotation. Individual processes run sequentially in their own working directories. The configuration's 4/8 GiB heap is intentional and is separate from the small smoke fixture.

The runner captures stdout and stderr together, records process return codes and wall time, and writes a manifest after each run. A nonzero return code, timeout, or missing passing marker causes a nonzero runner exit. GC log rotation is disabled for new runs. The original shell entry point name, `run_benchmarks.sh`, forwards to this Python runner.

Full DaCapo execution has not been verified in this environment because the benchmark JAR was not supplied. New-run commands target a compatible Linux/JDK setup. The runner writes selected-run metrics to its manifest; the archive-analysis command deliberately continues to read the historical packaged evidence, not arbitrary new trials.

## Measurement scope

| Metric | Definition and boundary |
| --- | --- |
| `final_iteration_ms` | Final matching DaCapo `PASSED in ... msec` marker, after warmups. It is not whole-JVM wall time. |
| `logged_pause_ms` | Sum of completed `GC(id) Pause ... Nms` records in primary `gc.log`, including startup, warmups, and harness-induced collections. |
| `logged_jvm_uptime_s` | Maximum logged JVM uptime. It approximates the logged lifetime, not external process wall time. |
| `logged_pause_fraction_pct` | `100 × logged_pause_ms / (1000 × logged_jvm_uptime_s)`. This is a whole-log fraction, not final-iteration GC overhead. |
| `pause_p99_ms` | Nearest-rank p99 of completed pause-event durations in one primary JVM log. For ZGC these are short pause phases, not concurrent-cycle durations or application request latency. |
| `mean_run_pause_p99_ms` | Arithmetic mean of those per-run p99 values over the shared workloads. It is not a pooled p99. |
| `geometric_runtime_ratio` | Geometric mean of per-workload final-runtime ratios relative to `parallel-4g-t4`, over the same 20 workloads. Lower is faster. |

Event start lines have no duration and are not counted. G1 remark/cleanup and ZGC pause phases are included when they have completed duration records. Decimal commas and decimal points are accepted. Concurrent work and periodic summary tables are excluded from stop-the-world statistics. Explicit `System.gc()` pauses are retained, so the tail includes harness behavior.

The two plotted runtime/pause axes describe different windows. The archive lacks timestamped application-phase boundaries sufficient to isolate GC pauses to the final iteration. A new rigorously aligned study would need callbacks or equivalent phase markers, independent process repetitions, and controlled host/JVM conditions. The Pareto frontier minimizes the declared numeric objectives only and is not a recommendation for every application.

## Archived evidence and historical metrics

`data/archive/*.jsonl.gz` retains 1,796 original text files in 616 records, grouped by workload. Each record contains the configuration name and a filename-to-text dictionary. All text was checked against the uploaded originals. The primary file is `gc.log`; `gc.log.0` sidecars are retained but excluded from current metrics. Sample sidecars restart uptime at zero and have earlier dates, so concatenating them would combine separate JVM runs without matching output.

All 28 configurations exist for each of 22 workload folders. Of these, 20 workloads have passing markers for all configurations. Cassandra and h2o have no passing marker in the supplied output and are classified as unconfirmed, not assigned zero runtime or treated as successful. The supplied per-benchmark CSV has 559 rows: it omits `pmd / g1-8g-p200-t8-c2`, although that primary output has a passing marker. Current reanalysis includes all 560 confirmed primary records.

The original CSVs, workbooks, and scripts are preserved separately. Their `total_gc_ms` and pause columns are not directly interchangeable with current metrics:

- The original runner sums G1/Parallel pauses across the JVM but divides by the final iteration's time, producing percentages above 100% for some workloads.
- Its ZGC regex reads periodic `Collector: Garbage Collection Cycle` summary values, including concurrent work, rather than actual pause-phase event durations.
- Its event counts divide detected start/end text counts by two, rather than counting only completed records. Its p99 falls back to the maximum for fewer than 100 observations.
- The original Pareto script filters `parallel-` configurations while labelling the plot G1. The current frontier uses the explicitly selected metrics and actual collector labels, including same-x dominance cases.

These historical files are retained as submitted. New figures are labelled as reanalysis and do not silently replace their values. Collector comparisons apply to this workload set and experiment environment. There are no confidence intervals or independent-repeat guarantees. The documents describe three repetitions, but three complete, independently identified sets cannot be recovered from the supplied archive. See the [research sources](RESEARCH.md) for original CPU/memory summaries, figures, and the historical lower-bound heuristic.

For background, see the [DaCapo reporting guidance](https://github.com/dacapobench/dacapobench) and [HotSpot ZGC documentation](https://docs.oracle.com/en/java/javase/21/gctuning/z-garbage-collector2.html). The supplied logs explicitly distinguish pause phases from concurrent-cycle statistics.

## Report

Build `docs/report/main.tex` with two pdfLaTeX passes. The Overleaf ZIP contains that source at its root and the required local figures. No shell escape or external conversion is needed.

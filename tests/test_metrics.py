import sys,unittest,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from metrics import parse_run,percentile
from analyze import pareto,analyze
from run_benchmarks import flags
class MetricsTests(unittest.TestCase):
 def test_completed_pauses_only_and_decimal_comma(self):
  log='[1,0s] GC(0) Pause Young (Normal)\n[1,2s] GC(0) Pause Young (Normal) 2M->1M(64M) 2,500ms\n[2.0s] GC(1) Pause Full (System.gc()) 1M->1M(64M) 1.5ms\n'
  r=parse_run('===== DaCapo version test PASSED in 12 msec =====',log,'test')
  self.assertEqual(r['pause_events'],2);self.assertEqual(r['logged_pause_ms'],4);self.assertEqual(r['young_pause_events'],1);self.assertEqual(r['full_pause_events'],1)
  self.assertEqual(r['logged_pause_fraction_pct'],.2)
 def test_zgc_summaries_are_not_pause_events(self):
  log='[1.0s] GC(2) Pause Mark Start 0.010ms\n[1.1s] GC(2) Concurrent Mark 50.000ms\n[1.2s] Collector: Garbage Collection Cycle 100 / 200 ms\n[1.3s] Phase: Pause Mark End 1 / 2 ms\n'
  r=parse_run('',log);self.assertEqual(r['pause_events'],1);self.assertEqual(r['logged_pause_ms'],.01);self.assertIsNone(r['final_iteration_ms']);self.assertEqual(r['status'],'unconfirmed')
 def test_nearest_rank_and_final_marker(self):
  self.assertEqual(percentile(list(range(1,101)),.99),99)
  s='===== DaCapo x bm completed warmup 1 in 99 msec =====\n===== DaCapo x bm PASSED in 20 msec =====\n===== DaCapo x bm PASSED in 15 msec ====='
  r=parse_run(s,'','bm');self.assertEqual(r['final_iteration_ms'],15);self.assertEqual(r['warmup_iterations'],1)
 def test_pareto_equal_x_and_dominated_points(self):
  rows=[{'x':1,'y':2},{'x':1,'y':1},{'x':2,'y':1},{'x':3,'y':.5}]
  self.assertEqual(pareto(rows,'x','y'),[rows[1],rows[3]])
 def test_config_flag_mapping(self):
  self.assertEqual(flags({'gc':'G1GC','xmx':'4g','pgc':4,'pause':50}),['-XX:+UseG1GC','-Xms4g','-Xmx4g','-XX:MaxGCPauseMillis=50','-XX:ParallelGCThreads=4'])
 def test_archive_coverage(self):
  with tempfile.TemporaryDirectory() as d:r=analyze(Path(d))
  self.assertEqual(r['primary_runs'],616);self.assertEqual(r['passed'],560);self.assertEqual(len(r['common_benchmarks']),20);self.assertEqual(len(r['configurations']),28);self.assertEqual(r['unconfirmed_benchmarks'],['cassandra','h2o'])
if __name__=='__main__':unittest.main()

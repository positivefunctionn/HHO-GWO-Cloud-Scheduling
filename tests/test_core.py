import unittest, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.overload import overload_label
from src.demand_adapter import adapt
from src.data_adapter import load_and_validate
from src.models import VM
from src.fitness import repair,evaluate
from src.baseline import best_fit_decreasing
from src.gwo import gwo
from src.hho import hho
from src.hybrid import hho_gwo
from src.pso import pso
from src.ga import ga
from src.sa import simulated_annealing
from src.aco import ant_colony
from src.de import differential_evolution
from src.woa import whale_optimization
from src.abc import artificial_bee_colony
from src.nsga2 import nsga2

CFG={'allowable_utilization':.8,'safe_utilization':.65,'risk_penalty':2,'execution_sla':1.5,'scheduling_interval':1,'weights':{'energy':.25,'makespan':.25,'sla':.25,'imbalance':.25},'normalization_references':{'energy':1000,'makespan':10,'sla':1,'imbalance':1},'hho':{'population_size':4,'iterations':3,'elite_size':2},'gwo':{'population_size':4,'iterations':3},'pso':{'population_size':4,'iterations':3},'ga':{'population_size':4,'iterations':3,'elite_count':2,'crossover_rate':.8,'mutation_rate':.08}}
ROWS=[{'predicted_cpu':'-2','p_overload':'.18','predicted_overload':'1'},{'predicted_cpu':'150','p_overload':'.1','predicted_overload':'0'}]
VMS=[VM('a','h',100,0,10,20),VM('b','h',100,0,10,20)]
class CoreTests(unittest.TestCase):

 def test_person1_csv_handoff_is_validated_without_changing_prediction_values(self):
  path=Path(__file__).resolve().parents[1]/"data"/"person2_scheduler_input.csv"
  rows,report=load_and_validate(path,expected_rows=1094,overload_threshold=80.0)
  self.assertTrue(report["valid"],report["errors"])
  self.assertEqual(len(rows),1094)
  self.assertEqual(report["schema"],"person1_bilstm_handoff")
  self.assertIn("not a calibrated probability",report["risk_score_source"])
  self.assertEqual(rows[0]["predicted_cpu"],float(rows[0]["bilstm_predicted_cpu"]))
  self.assertEqual(rows[0]["predicted_overload"],int(float(rows[0]["bilstm_predicted_overload"])))

 def test_evaluation_counter_counts_objective_calls(self):
  from src.fitness import reset_evaluation_count,get_evaluation_count
  tasks=adapt(ROWS,0,100,[])
  reset_evaluation_count()
  evaluate(tasks,[0,1],VMS,CFG)
  evaluate(tasks,[0,1],VMS,CFG)  # duplicate assignment is still a fresh objective call
  self.assertEqual(get_evaluation_count(),2)

 def test_optimizer_respects_objective_evaluation_budget(self):
  from src.fitness import reset_evaluation_count,get_evaluation_count
  tasks=adapt(ROWS,0,100,[])
  for optimizer in (gwo,hho,pso,ga,simulated_annealing,ant_colony,differential_evolution,whale_optimization,artificial_bee_colony,nsga2):
   reset_evaluation_count(limit=5)
   result=optimizer(tasks,VMS,CFG,7,max_evaluations=5)
   self.assertEqual(len(result[0]),len(tasks))
   self.assertEqual(get_evaluation_count(),5)
  reset_evaluation_count(limit=5)
  assignment,metrics,history,details=hho_gwo(tasks,VMS,CFG,7,max_evaluations=5)
  self.assertEqual(len(assignment),len(tasks))
  self.assertEqual(get_evaluation_count(),5)
  reset_evaluation_count()
 def test_threshold(self): self.assertEqual((overload_label(.17),overload_label(.18),overload_label(.9)),(0,1,1))
 def test_demand_repairs_only_negative(self):
  log=[]; ts=adapt(ROWS,0,100,log); self.assertEqual((ts[0].demand,ts[1].demand,len(log)),(0,150,1))
 def test_discrete_repair(self): self.assertEqual(repair([-9,.6,9],2),[0,1,1])
 def test_bfd_valid_and_metric(self):
  log=[]; ts=adapt(ROWS,0,100,log); a,m=best_fit_decreasing(ts,VMS,CFG); self.assertEqual(len(a),2); self.assertGreaterEqual(m.fitness,0)
 def test_zero_work(self):
  rows=[{'predicted_cpu':'0','p_overload':'0','predicted_overload':'0'}]; t=adapt(rows,0,100,[]); self.assertEqual(evaluate(t,[0],VMS,CFG).makespan,0)
 def test_gwo_hho_and_hybrid_return_valid_schedules(self):
  tasks=adapt(ROWS,0,100,[])
  for optimizer in (gwo,hho):
   assignment,metrics,history,_=optimizer(tasks,VMS,CFG,7)
   self.assertEqual(len(assignment),len(tasks)); self.assertTrue(all(i in (0,1) for i in assignment)); self.assertEqual(len(history),3); self.assertGreaterEqual(metrics.fitness,0)
  for optimizer in (pso,ga):
   assignment,metrics,history,_=optimizer(tasks,VMS,CFG,7)
   self.assertEqual(len(assignment),len(tasks)); self.assertTrue(all(i in (0,1) for i in assignment)); self.assertEqual(len(history),3); self.assertGreaterEqual(metrics.fitness,0)
  for optimizer in (simulated_annealing,ant_colony,differential_evolution,whale_optimization,artificial_bee_colony,nsga2):
   assignment,metrics,history,_=optimizer(tasks,VMS,CFG,7,max_evaluations=5)
   self.assertEqual(len(assignment),len(tasks)); self.assertTrue(all(i in (0,1) for i in assignment)); self.assertGreaterEqual(len(history),1); self.assertGreaterEqual(metrics.fitness,0)
  assignment,metrics,history,details=hho_gwo(tasks,VMS,CFG,7)
  self.assertEqual(len(assignment),len(tasks)); self.assertTrue(all(i in (0,1) for i in assignment)); self.assertEqual(details['hho_elite_count'],2); self.assertEqual(details['gwo_seeded_population'],4); self.assertEqual(len(history),6); self.assertGreaterEqual(metrics.fitness,0)

 def test_host_energy_counts_each_active_host_once_and_can_reward_consolidation(self):
  from src.models import Task
  from src.fitness import evaluate, reset_evaluation_count
  cfg=dict(CFG)
  cfg.update({"objective_mode":"three_term_host_energy_v1", "weights":{"energy":1/3,"sla":1/3,"makespan":1/3},
              "normalization_references":{"energy":410,"sla":1,"makespan":10}, "hosts":[
               {"host_id":"h1","cpu_capacity":200,"idle_power":100,"max_power":220},
               {"host_id":"h2","cpu_capacity":200,"idle_power":80,"max_power":190}]})
  tasks=[Task(i,0,20,0,0,20,actual_demand=20) for i in range(2)]
  vms=[VM('a','h1',100,0,0,0),VM('b','h1',100,0,0,0),VM('c','h2',100,0,0,0),VM('d','h2',100,0,0,0)]
  reset_evaluation_count()
  consolidated=evaluate(tasks,[0,1],vms,cfg)
  spread=evaluate(tasks,[0,2],vms,cfg)
  self.assertAlmostEqual(consolidated.energy,104.8)
  self.assertAlmostEqual(spread.energy,182.3)
  # The default exponent is convex (alpha=2); alpha=1 recovers the prior linear proxy.
  cfg_linear=dict(cfg); cfg_linear["host_power_curve_exponent"]=1.0
  linear=evaluate(tasks,[0,1],vms,cfg_linear)
  self.assertAlmostEqual(linear.energy,124.0)
  self.assertGreater(linear.energy,consolidated.energy)

 def test_invalid_host_power_curve_exponent_is_rejected(self):
  from src.models import Task
  from src.fitness import evaluate, reset_evaluation_count
  cfg=dict(CFG)
  cfg.update({"objective_mode":"three_term_host_energy_v1", "weights":{"energy":1/3,"sla":1/3,"makespan":1/3},
              "normalization_references":{"energy":410,"sla":1,"makespan":10}, "hosts":[
               {"host_id":"h1","cpu_capacity":200,"idle_power":100,"max_power":220}],
              "host_power_curve_exponent":0.5})
  task=Task(0,0,20,0,0,20,actual_demand=20)
  vms=[VM('a','h1',100,0,0,0)]
  reset_evaluation_count()
  with self.assertRaises(ValueError):
   evaluate([task],[0],vms,cfg)

 def test_realized_evaluation_uses_actual_demand_without_spending_search_budget(self):
  from src.models import Task
  from src.fitness import evaluate, evaluate_realized, reset_evaluation_count, get_evaluation_count
  cfg=dict(CFG)
  cfg.update({"objective_mode":"three_term_host_energy_v1", "weights":{"energy":1/3,"sla":1/3,"makespan":1/3},
              "normalization_references":{"energy":410,"sla":1,"makespan":10}, "hosts":[
               {"host_id":"h1","cpu_capacity":200,"idle_power":100,"max_power":220},
               {"host_id":"h2","cpu_capacity":200,"idle_power":80,"max_power":190}]})
  task=Task(0,0,20,0,0,20,actual_demand=40)
  vms=[VM('a','h1',100,0,0,0),VM('b','h1',100,0,0,0)]
  reset_evaluation_count(limit=3)
  predicted=evaluate([task],[0],vms,cfg)
  realized=evaluate_realized([task],[0],vms,cfg)
  self.assertNotEqual(predicted.makespan,realized.makespan)
  self.assertEqual(get_evaluation_count(),1)

if __name__=='__main__': unittest.main()

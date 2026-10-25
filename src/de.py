"""Discrete Differential Evolution baseline with a strict evaluation budget."""
import random
from .baseline import best_fit_decreasing
from .fitness import evaluate, get_evaluation_count, EvaluationBudgetExceeded

def differential_evolution(tasks, vms, cfg, seed, max_evaluations=300):
    rng=random.Random(seed); start=get_evaluation_count(); end=start+int(max_evaluations); n=len(tasks); m=len(vms)
    bfd,_=best_fit_decreasing(tasks,vms,cfg); bfd=list(bfd)
    if n==0 or m<2: return bfd, evaluate(tasks,bfd,vms,cfg), [], {"evaluations":get_evaluation_count()-start}
    pop_size=min(12,max(5, end-get_evaluation_count()))
    pop=[bfd]+[[rng.randrange(m) for _ in range(n)] for _ in range(pop_size-1)]
    vals=[]; archive=[]
    for x in pop:
        if get_evaluation_count()>=end: break
        try: met=evaluate(tasks,x,vms,cfg)
        except EvaluationBudgetExceeded: break
        vals.append(met); archive.append((list(x),met))
    F=float(cfg.get("de",{}).get("F",0.65)); CR=float(cfg.get("de",{}).get("CR",0.8))
    while get_evaluation_count()<end and pop and vals:
        for i in range(len(pop)):
            if get_evaluation_count()>=end: break
            others=[j for j in range(len(pop)) if j!=i]
            if len(others)<3: break
            a,b,c=rng.sample(others,3); jrand=rng.randrange(n); trial=[]
            for j in range(n):
                if j==jrand or rng.random()<CR: trial.append(int(round(pop[a][j]+F*(pop[b][j]-pop[c][j])))%m)
                else: trial.append(pop[i][j])
            try: met=evaluate(tasks,trial,vms,cfg)
            except EvaluationBudgetExceeded: break
            archive.append((list(trial),met))
            if met.fitness<=vals[i].fitness: pop[i],vals[i]=trial,met
    best,bmet=min(archive,key=lambda p:p[1].fitness)
    return best,bmet,[p[1].fitness for p in archive],{"evaluations":get_evaluation_count()-start}

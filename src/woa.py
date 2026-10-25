"""Discrete Whale Optimization Algorithm baseline with a strict evaluation budget."""
import math, random
from .baseline import best_fit_decreasing
from .fitness import evaluate, get_evaluation_count, EvaluationBudgetExceeded

def whale_optimization(tasks,vms,cfg,seed,max_evaluations=300):
    rng=random.Random(seed); start=get_evaluation_count(); end=start+int(max_evaluations); n=len(tasks); m=len(vms)
    bfd,_=best_fit_decreasing(tasks,vms,cfg); bfd=list(bfd)
    if n==0 or m<2: return bfd,evaluate(tasks,bfd,vms,cfg),[],{"evaluations":get_evaluation_count()-start}
    size=min(10,max(4,end-get_evaluation_count())); pos=[[float(x) for x in bfd]]+[[rng.uniform(0,m-1) for _ in range(n)] for _ in range(size-1)]
    archive=[]; fitness=[]
    for p in pos:
        if get_evaluation_count()>=end: break
        a=[max(0,min(m-1,int(round(z)))) for z in p]
        try: met=evaluate(tasks,a,vms,cfg)
        except EvaluationBudgetExceeded: break
        archive.append((a,met)); fitness.append(met.fitness)
    while get_evaluation_count()<end and pos and fitness:
        bi=min(range(len(fitness)),key=lambda i:fitness[i]); best=pos[bi][:]
        for i in range(len(pos)):
            if get_evaluation_count()>=end: break
            r=rng.random(); A=2*(1-rng.random()); C=2*rng.random(); l=rng.uniform(-1,1); a=2*(1-get_evaluation_count()/max(1,end-start))
            new=[]
            for j,x in enumerate(pos[i]):
                if rng.random()<0.5:
                    if abs(A)<1:
                        d=abs(C*best[j]-x); y=best[j]-A*d
                    else:
                        peer=pos[rng.randrange(len(pos))][j]; d=abs(C*peer-x); y=peer-A*d
                else:
                    d=abs(best[j]-x); y=d*math.exp(1.0*l)*math.cos(2*math.pi*l)+best[j]
                new.append(max(0.0,min(m-1.0,y)))
            assignment=[int(round(z)) for z in new]
            try: met=evaluate(tasks,assignment,vms,cfg)
            except EvaluationBudgetExceeded: break
            archive.append((assignment,met))
            if met.fitness<=fitness[i]: pos[i]=new; fitness[i]=met.fitness
    best,bmet=min(archive,key=lambda p:p[1].fitness)
    return best,bmet,[p[1].fitness for p in archive],{"evaluations":get_evaluation_count()-start}

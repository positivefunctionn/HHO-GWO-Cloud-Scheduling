"""Discrete Artificial Bee Colony baseline with a strict evaluation budget."""
import random
from .baseline import best_fit_decreasing
from .fitness import evaluate, get_evaluation_count, EvaluationBudgetExceeded

def artificial_bee_colony(tasks,vms,cfg,seed,max_evaluations=300):
    rng=random.Random(seed); start=get_evaluation_count(); end=start+int(max_evaluations); n=len(tasks); m=len(vms)
    bfd,_=best_fit_decreasing(tasks,vms,cfg); bfd=list(bfd)
    if n==0 or m<2: return bfd,evaluate(tasks,bfd,vms,cfg),[],{"evaluations":get_evaluation_count()-start}
    size=min(10,max(4,end-get_evaluation_count())); food=[bfd]+[[rng.randrange(m) for _ in range(n)] for _ in range(size-1)]; vals=[]; trials=[0]*len(food); archive=[]
    for x in food:
        if get_evaluation_count()>=end: break
        try: met=evaluate(tasks,x,vms,cfg)
        except EvaluationBudgetExceeded: break
        vals.append(met); archive.append((list(x),met))
    food=food[:len(vals)]; trials=trials[:len(vals)]; limit=max(5,2*n//max(1,len(food)))
    while get_evaluation_count()<end and food:
        for i in range(len(food)):
            if get_evaluation_count()>=end: break
            k=rng.choice([j for j in range(len(food)) if j!=i]) if len(food)>1 else i
            cand=list(food[i]); j=rng.randrange(n); cand[j]=rng.randrange(m) if rng.random()<0.25 else (cand[j]+rng.choice([-1,1]))%m
            try: met=evaluate(tasks,cand,vms,cfg)
            except EvaluationBudgetExceeded: break
            archive.append((cand,met))
            if met.fitness<vals[i].fitness: food[i],vals[i],trials[i]=cand,met,0
            else: trials[i]+=1
        if get_evaluation_count()>=end: break
        # Onlooker phase: roulette selection by inverse fitness, then one-neighbor search.
        weights=[1/(1e-9+max(0.0,v.fitness)) for v in vals]; total=sum(weights)
        for _ in range(len(food)):
            if get_evaluation_count()>=end: break
            i=rng.choices(range(len(food)),weights=weights,k=1)[0]; cand=list(food[i]); j=rng.randrange(n); cand[j]=rng.randrange(m)
            try: met=evaluate(tasks,cand,vms,cfg)
            except EvaluationBudgetExceeded: break
            archive.append((cand,met))
            if met.fitness<vals[i].fitness: food[i],vals[i],trials[i]=cand,met,0
            else: trials[i]+=1
        for i,t in enumerate(trials):
            if t>=limit and get_evaluation_count()<end:
                cand=[rng.randrange(m) for _ in range(n)]
                try: met=evaluate(tasks,cand,vms,cfg)
                except EvaluationBudgetExceeded: break
                archive.append((cand,met)); food[i],vals[i],trials[i]=cand,met,0
    best,bmet=min(archive,key=lambda p:p[1].fitness)
    return best,bmet,[p[1].fitness for p in archive],{"evaluations":get_evaluation_count()-start}

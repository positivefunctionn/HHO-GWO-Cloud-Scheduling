"""NSGA-II multiobjective baseline for energy, SLA rate and makespan."""
import random
from .baseline import best_fit_decreasing
from .fitness import evaluate, get_evaluation_count, EvaluationBudgetExceeded

def _obj(m): return (m.energy,m.sla_violation_count,m.makespan)
def _dominates(a,b):
    x,y=_obj(a),_obj(b); return all(i<=j for i,j in zip(x,y)) and any(i<j for i,j in zip(x,y))
def _fronts(pop):
    dominates=[[] for _ in pop]; count=[0]*len(pop); fronts=[[]]
    for i,(_,mi) in enumerate(pop):
        for j,(_,mj) in enumerate(pop):
            if i==j: continue
            if _dominates(mi,mj): dominates[i].append(j)
            elif _dominates(mj,mi): count[i]+=1
        if count[i]==0: fronts[0].append(i)
    k=0
    while k<len(fronts) and fronts[k]:
        nxt=[]
        for i in fronts[k]:
            for j in dominates[i]:
                count[j]-=1
                if count[j]==0: nxt.append(j)
        if nxt: fronts.append(nxt)
        k+=1
    return fronts
def _crowding(front,pop):
    dist={i:0.0 for i in front}
    if len(front)<=2: return {i:float('inf') for i in front}
    for attr in (lambda m:m.energy,lambda m:m.sla_violation_count,lambda m:m.makespan):
        ordered=sorted(front,key=lambda i:attr(pop[i][1])); dist[ordered[0]]=dist[ordered[-1]]=float('inf'); lo=attr(pop[ordered[0]][1]); hi=attr(pop[ordered[-1]][1])
        if hi>lo:
            for q in range(1,len(ordered)-1): dist[ordered[q]]+=(attr(pop[ordered[q+1]][1])-attr(pop[ordered[q-1]][1]))/(hi-lo)
    return dist
def nsga2(tasks,vms,cfg,seed,max_evaluations=300):
    rng=random.Random(seed); start=get_evaluation_count(); end=start+int(max_evaluations); n=len(tasks); m=len(vms)
    bfd,_=best_fit_decreasing(tasks,vms,cfg); bfd=list(bfd)
    if n==0 or m<2: return bfd,evaluate(tasks,bfd,vms,cfg),[],{"evaluations":get_evaluation_count()-start}
    size=min(20,max(6,end-get_evaluation_count())); candidates=[bfd]+[[rng.randrange(m) for _ in range(n)] for _ in range(size-1)]; pop=[]; archive=[]
    for a in candidates:
        if get_evaluation_count()>=end: break
        try: met=evaluate(tasks,a,vms,cfg)
        except EvaluationBudgetExceeded: break
        pop.append((a,met)); archive.append((list(a),met))
    while get_evaluation_count()<end and pop:
        fronts=_fronts(pop); rank={i:r for r,f in enumerate(fronts) for i in f}; crowd={i:d for f in fronts for i,d in _crowding(f,pop).items()}; children=[]
        def tournament():
            i,j=rng.randrange(len(pop)),rng.randrange(len(pop)); return i if (rank[i],-crowd[i])<(rank[j],-crowd[j]) else j
        for _ in range(min(size,end-get_evaluation_count())):
            if get_evaluation_count()>=end: break
            p1,p2=pop[tournament()][0],pop[tournament()][0]; child=[]
            for j in range(n):
                val=p1[j] if rng.random()<0.5 else p2[j]
                if rng.random()<0.15: val=rng.randrange(m)
                child.append(val)
            try: met=evaluate(tasks,child,vms,cfg)
            except EvaluationBudgetExceeded: break
            children.append((child,met)); archive.append((list(child),met))
        combined=pop+children; chosen=[]
        for front in _fronts(combined):
            if len(chosen)+len(front)<=size: chosen.extend(front)
            else:
                cd=_crowding(front,combined); chosen.extend(sorted(front,key=lambda i:cd[i],reverse=True)[:size-len(chosen)]); break
        pop=[combined[i] for i in chosen]
    best,bmet=min(archive,key=lambda p:p[1].fitness)
    return best,bmet,[p[1].fitness for p in archive],{"evaluations":get_evaluation_count()-start,"pareto_archive_size":len(_fronts(archive)) if archive else 0}

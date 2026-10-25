from .fitness import evaluate

def best_fit_decreasing(tasks,vms,cfg):
    assignment=[0]*len(tasks); loads=[v.current_cpu_load for v in vms]
    for original_i, task in sorted(enumerate(tasks), key=lambda item:(-item[1].demand,item[1].task_id)):
        choices=[]
        for i,vm in enumerate(vms):
            u=(loads[i]+task.demand)/vm.cpu_capacity; feasible=u<=cfg["allowable_utilization"]
            # normal BFD tight fit; high-risk task adds a transparent unsafe-placement cost
            cost=(0 if feasible else 1000)+abs(cfg["allowable_utilization"]-u)+(task.p_overload*max(0,u-cfg["safe_utilization"]) if task.predicted_overload else 0)
            choices.append((cost,i))
        idx=min(choices)[1]; assignment[original_i]=idx; loads[idx]+=task.demand
    return assignment,evaluate(tasks,assignment,vms,cfg)

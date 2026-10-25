TAU = 0.18
def overload_label(probability, tau=TAU):
    if not 0 <= probability <= 1: raise ValueError("probability must be in [0,1]")
    return int(probability >= tau)

def risk_cost(task, utilization, safe_utilization, penalty):
    return penalty * task.p_overload * max(0.0, utilization-safe_utilization) if task.predicted_overload else 0.0

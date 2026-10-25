from dataclasses import dataclass

@dataclass(frozen=True)
class Task:
    task_id: int
    horizon_id: int
    predicted_cpu: float
    p_overload: float
    predicted_overload: int
    demand: float
    actual_cpu: float = 0.0       # evaluation-only; never used by the optimizer
    timestamp: float = 0.0        # source timestamp retained for traceability
    actual_demand: float | None = None  # evaluation-only demand; optimizer must not read this

@dataclass(frozen=True)
class VM:
    vm_id: str
    host_id: str
    cpu_capacity: float
    current_cpu_load: float
    idle_power: float
    max_power: float

@dataclass
class ScheduleMetrics:
    fitness: float
    energy: float
    makespan: float
    sla_violation_count: int
    load_imbalance: float
    average_utilization: float
    overload_count: int

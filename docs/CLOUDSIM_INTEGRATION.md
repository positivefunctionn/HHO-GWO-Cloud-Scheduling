# Person 3 handoff

Consume `schedule_results.csv`: `task_id → Cloudlet ID`, `selected_vm_id → CloudSim VM ID`, and configured `host_id → CloudSim Host ID`. The Python `CloudSimAdapterInterface` is intentionally abstract and imports no CloudSim libraries. Person 3 should use the mapping to build Cloudlets and VMs, then perform authoritative energy, SLA, makespan, utilization, response-time, throughput, and load-balancing evaluation. The Python values are proxy optimization metrics, not Bitbrain infrastructure measurements.

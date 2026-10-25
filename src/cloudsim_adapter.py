from abc import ABC,abstractmethod
class CloudSimAdapterInterface(ABC):
    """Person 3 implements this without changing optimizer code."""
    @abstractmethod
    def translate(self, task_id, horizon_id, selected_vm_id, host_id): pass

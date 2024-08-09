"""
Contains models for GPU and GPUProcess
"""

from typing import Dict, List

from pydantic import BaseModel

from experiment_runner.utils import safe_float_cast


class GPU(BaseModel):
    """
    Data class for GPU Info
    """

    id: int
    uuid: str
    load: float
    memory_total: int
    memory_used: int
    memory_free: int
    driver: str
    name: str
    serial: str
    display_mode: str
    display_active: str
    temperature: float

    def to_dict(self) -> Dict[str, str]:
        """
        Convert GPU object to a dictionary all float values will be convereted to strings with two decimal places
        """
        tmp_dict = {**self.dict(), "memory_util": self.memory_util}
        # create new dict ret and format all numbers in tmp_dict as string with two decimal places
        ret = {key: f"{value:.2f}" if isinstance(value, float) else str(value) for key, value in tmp_dict.items()}
        return ret

    @property
    def memory_util(self):
        """
        Calculates relative memory usage
        """
        return float(self.memory_used) / float(self.memory_total)

    def __hash__(self):
        return hash(self.uuid)

    @classmethod
    def from_nvidia_smi_list(cls, line: List[str]):
        """
        Parses a given nvidia-smi output line into a GPU object
        Args:
            line: List of str representing one GPU

        Returns:
            The created GPU DTO
        """
        return cls(
            id=int(line[0]),
            uuid=line[1].strip(),
            load=safe_float_cast(line[2]) / 100,
            memory_total=int(line[3]),
            memory_used=int(line[4]),
            memory_free=int(line[5]),
            driver=line[6].strip(),
            name=line[7].strip(),
            serial=line[8].strip(),
            display_mode=line[10].strip(),
            display_active=line[9].strip(),
            temperature=safe_float_cast(line[11]),
        )

    def is_available(self, max_load: float = 0.5, max_memory: float = 0.5, memory_free: float = 0) -> bool:
        """
        Checks whether a GPU is considered availaible (within the given load parameters)
        Args:
            max_load: Max load of the GPU to be considered available
            max_memory: Max memory of the GPU to be considered available
            memory_free: Minmum amount of free memory to be considered available

        Returns:
            True if the GPU is available else False
        """
        return (self.load <= max_load) and (self.memory_util <= max_memory) and (self.memory_free >= memory_free)


class GPUProcess(BaseModel):
    """
    DTO representing a running GPU Process
    """

    pid: int
    process_name: str
    gpu_uuid: str

    @classmethod
    def from_nvidia_smi_list(cls, line: List[str]):
        """
        Parses a given nvidia-smi output line into a GPUProcess object
        Args:
            line: List of str representing one GPUProcess

        Returns:
            The created GPUProcess DTO
        """
        return cls(pid=int(line[0]), process_name=line[1].strip(), gpu_uuid=line[2].strip())

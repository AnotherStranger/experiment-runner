"""
GPUProvider retrieve GPU-Information
"""

import csv
import os
import subprocess
from abc import ABC, abstractmethod
from typing import Iterator, List

from experiment_runner.processing.gpu.exceptions import GPUNotFoundException
from experiment_runner.processing.gpu.models import GPU, GPUProcess


class GPUProvider(ABC):
    """
    This class describes the interface to get GPU informations
    """

    @abstractmethod
    def get_compute_processes(self) -> List[GPUProcess]:
        """
        Returns a list all currently active compute processes
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def gpus(self) -> list[GPU]:
        """
        Returns a list of all installed GPUs of this type provider
        """
        raise NotImplementedError()


class NvidiaGPUProvider(GPUProvider):
    """
    This class defines the GPU Provider for Nvidia GPUs
    """

    def __init__(self, nvidia_smi_path: str = "nvidia-smi"):
        self.nvidia_smi_path = nvidia_smi_path

    def _run_nvidia_smi(self, params: List[str]) -> Iterator[List[str]]:
        output = ""
        try:
            process = subprocess.run(
                [self.nvidia_smi_path] + params,
                check=True,
                capture_output=True,
                text=True,
            )
            output = process.stdout

        except FileNotFoundError as exc:
            raise GPUNotFoundException("🚨 File 'nvidia-smi' not found. 🚨") from exc

        except subprocess.CalledProcessError as ex:
            raise ValueError("Could not call nvidia-smi command. Please check your path.") from ex

        lines = [line for line in output.split(os.linesep) if line]

        return csv.reader(lines, delimiter=",")

    def get_compute_processes(self) -> List[GPUProcess]:
        """
        Returns all currently active Nvidia compute processes
        """
        reader = self._run_nvidia_smi(
            ["--query-compute-apps=pid,process_name,gpu_uuid", "--format=csv,noheader,nounits"]
        )

        return [GPUProcess.from_nvidia_smi_list(line) for line in reader]

    @property
    def gpus(self) -> List[GPU]:
        """
        Returns a list of all installed Nvidia GPUs
        """
        reader = self._run_nvidia_smi(
            [
                "--query-gpu=index,uuid,utilization.gpu,memory.total,memory.used,memory.free,driver_version,name,"
                "gpu_serial,display_active,display_mode,temperature.gpu",
                "--format=csv,noheader,nounits",
            ]
        )

        gpus = [GPU.from_nvidia_smi_list(line) for line in reader]

        return gpus

"""
Contains managers to handle GPU (and later CPU and TPU?)
"""

import grp
import pwd
from typing import List, Set, Tuple

import psutil

from experiment_runner.processing.gpu.models import GPU
from experiment_runner.processing.gpu.providers import GPUProvider, NvidiaGPUProvider
from experiment_runner.processing.gpu.strategies import (
    SelectionStrategy,
    SelectionStrategyEnum,
    SelectionStrategyFactory,
)
from experiment_runner.utils import get_user_for_pid

STAFF_GROUP_NAME: str = "mitarbeiter"  # This group is for more privileged users
MAX_GPUS_PER_STAFF: int = 10  # This defines the max GPUs for the privileged user
MAX_GPUS_PER_OTHER: int = 1  # This defines the max GPUs for all other users (e.g. students)


class GPUManager:
    """
    This class is used to query (Nvidia) GPU information
    """

    def __init__(
        self,
        selection_strategy: SelectionStrategy = SelectionStrategyFactory.get_instance(SelectionStrategyEnum.FIRST),
        provider: GPUProvider = NvidiaGPUProvider(),
    ):
        self.gpu_provider: GPUProvider = provider
        self.strategy = selection_strategy

    @property
    def gpus(self) -> List[GPU]:
        """
        Returns a list of all installed GPUs
        """
        return self.gpu_provider.gpus

    @property
    def active_users(self) -> Set[str]:
        """
        Creates a list of all usernames with running GPU processes
        Returns:
            Set of users active on one or more GPUs
        """
        processes = self.gpu_provider.get_compute_processes()
        users = {get_user_for_pid(process.pid) for process in processes}
        return {user for user in users if user is not None}

    @property
    def username(self) -> str:
        """
        Gets the name of the current user
        """
        name: str = psutil.Process().username()
        return name

    def __getitem__(self, uuid: str) -> GPU:
        """
        Allows using the bracket operator to access GPUs by their IDs

        Args:
            uuid (str): uuid of the wanted GPU
        """

        for gpu in self.gpus:
            if gpu.uuid == uuid:
                return gpu
        raise ValueError("The given GPU UUID does not exist.")

    def get_groups_of_current_user(self) -> List[str]:
        """
        Returns a list of all groups of the current user
        """
        groups = [g.gr_name for g in grp.getgrall() if self.username in g.gr_mem]
        gid = pwd.getpwnam(self.username).pw_gid
        groups.append(grp.getgrgid(gid).gr_name)
        return groups

    def get_gpus_of_current_user(self):
        """
        Returns a list of all GPUs currently in use by the active user
        """
        return self.get_gpus_of_user(self.username)

    def get_gpu_processes_of_user(self, username: str):
        """
        Returns a List of all active gpu processes of the given user
        Args:
            username: user to get the gpu processes for

        Returns:
            List of GPU processes for user
        """
        return [
            gpu_process
            for gpu_process in self.gpu_provider.get_compute_processes()
            if get_user_for_pid(gpu_process.pid) == username
        ]

    def get_gpus_of_user(self, username: str) -> Set[GPU]:
        """
        Returns a list of all GPUs currently in use by the given user
        """

        gpus_used_by_current_user = {
            self[gpu_process.gpu_uuid] for gpu_process in self.get_gpu_processes_of_user(username)
        }

        return {gpu for gpu in gpus_used_by_current_user if gpu is not None}

    def get_gpu_limit_of_current_user(self) -> int:
        """
        Return the total number of gpus the current user is allowed to use
        """
        return MAX_GPUS_PER_STAFF if STAFF_GROUP_NAME in self.get_groups_of_current_user() else MAX_GPUS_PER_STAFF

    def get_available(
        self,
        limit=1,
        max_load=0.5,
        max_memory=0.5,
        memory_free=0,
    ) -> List[GPU]:
        """
        Returns all available GPUs sorted by order with no load higher than max_load
        and no memory_usage higher than max_memory
        """

        # Get device IDs, load and memory usage
        gpus = [
            gpu
            for gpu in self.gpus
            if gpu.is_available(max_load=max_load, max_memory=max_memory, memory_free=memory_free)
        ]

        # Sort available GPUs according to the configured strategy
        gpus = self.strategy(gpus)

        total_gpus = len(gpus)
        available_gpus_for_current_user = self.get_gpu_limit_of_current_user() - len(self.get_gpus_of_current_user())

        upper_limit = min(total_gpus, available_gpus_for_current_user, limit)
        gpus = gpus[0:upper_limit]
        return gpus

    def create_utilization_table(self, attributes: Tuple[str, ...] = ("load", "memory_util", "temperature")) -> str:
        """
        Creates a markdown table containing the selected information
        """
        gpus = self.gpus
        column_name_mapping = {
            "id": "ID",
            "name": "Name",
            "serial": "Serial",
            "uuid": "UUID",
            "temperature": "GPU temp.",
            "load": "GPU util.",
            "memory_util": "Memory util.",
            "memory_total": "Memory total",
            "memory_used": "Memory used",
            "memory_free": "Memory free",
            "display_mode": "Display mode",
            "display_active": "Display active",
        }

        attributes = ("id",) + attributes
        # Get max len for each field in gpus
        max_len = {
            attr: max([len(str(gpu.to_dict()[attr])) for gpu in gpus] + [len(column_name_mapping[attr])])
            for attr in attributes
        }

        header = "| "
        seperator = "|"
        formatstring = "| "
        for attr in attributes:
            name = attr
            header += f"{column_name_mapping[attr]:^{max_len[attr]}s} | "
            seperator += f"{'-' * (max_len[attr]+1)}-|"
            formatstring += f"{{{name}:^{max_len[attr]}}} | "

        lines = [header, seperator]
        for gpu in gpus:
            gdict = gpu.to_dict()
            lines.append(formatstring.format(**gdict))

        return "\n".join(lines)

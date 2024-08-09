"""
This module handles the execution of subcommands in processes.
"""

# pylint: disable=too-few-public-methods
import atexit
import os
import shlex
import subprocess
import sys
from typing import Dict, List, Optional

import typer
from rich import print  # pylint: disable=redefined-builtin

from experiment_runner.processing.callbacks import Callback
from experiment_runner.processing.gpu.models import GPU


class CommandRunner:
    """
    Class for running shell commands in a subprocess.
    """

    def __init__(self, callbacks: Optional[List[Callback]] = None) -> None:
        """
        Initializes a command runner.

        Args:
            callbacks: A list of callbacks to be called on start and end of the command.
        """
        self.callbacks = callbacks or []

    def register_callback(self, callback: Callback):
        """
        Register a callback to the runner
        """
        self.callbacks.append(callback)

    def _invoke_callbacks(self, method_name, *args, **kwargs):
        for callback in self.callbacks:
            method = getattr(callback, method_name, None)
            if method:
                try:
                    method(*args, **kwargs)
                except Exception as err:  # pylint: disable=broad-exception-caught
                    print(f"Error in callback method '{method_name}': {err}")

    def __on_start(self, command):
        self._invoke_callbacks("on_start", command)

    def __on_end(self, command, returncode):
        self._invoke_callbacks("on_end", command, returncode)
        if returncode == 0:
            self._invoke_callbacks("on_success", command, returncode)
        else:
            self._invoke_callbacks("on_error", command, returncode)

    def __on_log(self, command, log):
        self._invoke_callbacks("on_log", command, log)

    def run_gpu(self, command: str, gpus: List[GPU]) -> int:
        """
        Uses run to run with specified gpus

        Args:
            command: The command to run.
            gpus: List of GPU which will be available for the run command

        Return:
            The return code of the command. Or -1 if the command could not be run.
        """
        typer.echo(f"{typer.style('🚀 Running:', fg=typer.colors.GREEN, bold=True)} {command}")

        return self.run(
            command,
            additional_env={
                "CUDA_DEVICE_ORDER": "PCI_BUS_ID",
                "CUDA_VISIBLE_DEVICES": f"{','.join([str(cuda_device.id) for cuda_device in gpus])}" if gpus else "",
            },
        )

    def run(self, command: str, additional_env: Dict[str, str]) -> int:
        """
        Uses subprocess library to run a given command.

        Args:
            command: The command to run.
            additional_env: Additional environment variables to set.

        Returns:
            The return code of the command. Or -1 if the command could not be run.
        """

        self.__on_start(command)

        env = os.environ
        for key, value in additional_env.items():
            env[key] = value

        returncode = -1
        try:
            with subprocess.Popen(
                shlex.split(command),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf8",
                universal_newlines=True,
            ) as process:
                atexit.register(process.kill)

                # Read and print the subprocess output immediately
                for line in process.stdout:  # type: ignore
                    print(
                        line.encode(sys.stdout.encoding, errors="replace").decode(sys.stdout.encoding),
                        end="",
                    )
                    self.__on_log(command, line)
                    sys.stdout.flush()  # type: ignore

                process.wait()
                atexit.unregister(process.kill)
                returncode = process.returncode
        except RuntimeError as err:
            print(f"Error in run_command: {err}")
        finally:
            self.__on_end(command, returncode)

        return returncode

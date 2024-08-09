"""
This module provides the main cmd interface
"""

import sys
from pathlib import Path
from time import sleep
from typing import List

import typer
from rich import print  # pylint: disable=redefined-builtin

from experiment_runner import __version__
from experiment_runner.processing.callbacks import LoggerCallback, MailerCallback
from experiment_runner.processing.configurator import CONFIG_PATH, Configurator
from experiment_runner.processing.gpu.exceptions import GPUNotFoundException
from experiment_runner.processing.gpu.manager import GPU, GPUManager
from experiment_runner.processing.gpu.strategies import (
    SelectionStrategyEnum,
    SelectionStrategyFactory,
)
from experiment_runner.processing.mail import Mailer
from experiment_runner.processing.subprocesses import CommandRunner

app = typer.Typer()

# Wait-for-GPUS Polling rate
POLLING_RATE_IN_SECONDS = 1.0


@app.command()
def run(
    command: str,
    gpu_selection: SelectionStrategyEnum = typer.Option(
        SelectionStrategyEnum.LOAD_MEMORY_RANDOM.value,
        help="Strategy for GPU selection. No GPU will be available if none",
    ),
    num_gpus: int = typer.Option(1, help="Desired number of GPUs. Not guaranteed."),
    send_mail: bool = typer.Option(False, help="Send email after experiment finishes or fails."),
    wait_for_gpus: bool = typer.Option(False, help="Wait until num_gpus are available."),
    logging: Path = typer.Option(None, help="Write all output into a file at this location."),
    config_path: Path = typer.Option(CONFIG_PATH, help=f"Use this configuration file.(Default: {CONFIG_PATH})"),
):
    """
    Runs a specified command
    """

    Configurator().load_config(config_path)
    manager = GPUManager(SelectionStrategyFactory.get_instance(gpu_selection))
    runner = CommandRunner()

    if send_mail or Configurator().config.use_mailer:
        runner.register_callback(MailerCallback(Mailer(), logging))
    if logging:
        runner.register_callback(LoggerCallback(logging))

    cuda_devices: List[GPU] = []
    return_code = 1
    try:
        if manager.get_gpu_limit_of_current_user() < num_gpus:
            typer.echo(
                "🚨 "
                + typer.style(
                    "Your requested number of GPUs is not allowed for your user group."
                    + f"({manager.get_gpu_limit_of_current_user()}/{num_gpus} GPUs are allowed)",
                    fg=typer.colors.WHITE,
                    bg=typer.colors.RED,
                    bold=True,
                    blink=True,
                )
                + " 🚨"
            )
        elif len(manager.gpus) < num_gpus:
            typer.echo(
                "🚨 "
                + typer.style(
                    "Your requested number of GPUs is not available on this device."
                    + f"({len(manager.gpus)}/{num_gpus} GPUs avaliable.)",
                    fg=typer.colors.WHITE,
                    bg=typer.colors.RED,
                    bold=True,
                    blink=True,
                )
                + " 🚨"
            )
        else:
            while len(cuda_devices) < num_gpus:
                # Check cuda devices available
                cuda_devices = list(manager.get_gpus_of_current_user())
                if len(cuda_devices) < num_gpus:
                    cuda_devices = manager.get_available(limit=num_gpus)

                if len(cuda_devices) != num_gpus:
                    typer.echo(
                        "🚨 "
                        + typer.style(
                            "Your requested number of GPUs is not available."
                            + f"({len(cuda_devices)}/{num_gpus} GPUs are available)",
                            fg=typer.colors.WHITE,
                            bg=typer.colors.RED,
                            bold=True,
                            blink=True,
                        )
                        + " 🚨"
                    )

                if not wait_for_gpus:
                    break

                sleep(Configurator().config.polling_rate_in_seconds)
            return_code = runner.run_gpu(command, cuda_devices)
    except GPUNotFoundException as err:
        typer.echo(
            typer.style(
                f"{err}",
                fg=typer.colors.WHITE,
                bg=typer.colors.RED,
                bold=True,
                blink=True,
            )
        )
        if typer.confirm("🚨 Do you want to continue without nvidia-smi? 🚨"):
            return_code = runner.run_gpu(command, cuda_devices)
    return return_code


@app.command()
def gpu_info(attributes: List[str] = typer.Option(["load", "memory_util", "temperature"])):
    """
    Prints current GPU util
    """
    try:
        manager = GPUManager()
        util_table = manager.create_utilization_table(tuple(attributes))
        typer.echo(util_table)

    except GPUNotFoundException as err:
        typer.echo(
            typer.style(
                f"{err}",
                fg=typer.colors.WHITE,
                bg=typer.colors.RED,
                bold=True,
                blink=True,
            )
        )


@app.command()
def print_gpus_env(
    gpu_selection: SelectionStrategyEnum = typer.Option(
        SelectionStrategyEnum.LOAD_MEMORY_RANDOM.value,
        help="Strategy for GPU selection. No GPU will be available if none",
    ),
    num_gpus: int = typer.Option(1, help="Desired number of GPUs. Not guaranteed."),
):
    """
    Creates an environment variable of maximum num_gpus available.
    Use `export $(experiment print-gpus-env)` to only make a subset of gpus available.
    """
    try:
        manager = GPUManager(SelectionStrategyFactory.get_instance(gpu_selection))
        cuda_devices = list(manager.get_gpus_of_current_user())
        if len(cuda_devices) == 0:
            cuda_devices = manager.get_available(limit=num_gpus)

        cuda_devices_str = ",".join([str(device.id) for device in cuda_devices])
        print(f"CUDA_VISIBLE_DEVICES={cuda_devices_str}")
    except GPUNotFoundException as err:
        typer.echo(
            typer.style(
                f"{err}",
                fg=typer.colors.WHITE,
                bg=typer.colors.RED,
                bold=True,
                blink=True,
            )
        )


@app.command()
def gpu_usage_report():
    """
    Prints a GPU usage report for all currently active Users
    """
    try:
        manager = GPUManager()

        for user in manager.active_users:
            typer.echo(f"Report for user {user}:")

            used_gpus = sorted([gpu.id for gpu in manager.get_gpus_of_user(user)])
            used_gpus_str = f"\tUsed GPUs: {used_gpus}"
            if len(used_gpus) > 1:
                typer.echo(typer.style(used_gpus_str, fg=typer.colors.WHITE, bg=typer.colors.RED, bold=True))
            else:
                typer.echo(used_gpus_str)

            typer.echo(f"\tPIDs: {sorted([proc.pid for proc in manager.get_gpu_processes_of_user(user)])}")
            typer.echo()
    except GPUNotFoundException as err:
        typer.echo(
            typer.style(
                f"{err}",
                fg=typer.colors.WHITE,
                bg=typer.colors.RED,
                bold=True,
                blink=True,
            )
        )


@app.command()
def version():
    """
    Prints the program version
    """
    print(__version__)


@app.command()
def create_config(
    config_path: Path = typer.Option(CONFIG_PATH, help=f"Use this configuration file.(Default: {CONFIG_PATH})")
):
    """
    Create or edit configuration file
    """
    Configurator().config_path = config_path
    Configurator().create_config()


@app.command()
def show_config(
    config_path: Path = typer.Option(CONFIG_PATH, help=f"Use this configuration file.(Default: {CONFIG_PATH})")
):
    """
    Displays the specified configuration parameters
    """
    Configurator().config_path = config_path
    Configurator().show_config()


@app.command()
def test_mail(
    config_path: Path = typer.Option(CONFIG_PATH, help=f"Use this configuration file.(Default: {CONFIG_PATH})"),
    subject: str = typer.Argument(..., help="Subject of the E-Mail"),
    message: str = typer.Argument(..., help="Text for the E-Mail body"),
):
    """
    Sends a mail using the Mailer. Useful for testing your settings.
    """

    Configurator().config_path = config_path
    mailer = Mailer()

    try:
        mailer.send(subject, message)
    except Exception as err:  # pylint: disable=broad-exception-caught
        print(f"An error occoured while sending an E-Mail: {err}")
        sys.exit(-1)


def main_cmd():
    """
    Entrypoint for poetry scripts
    """
    app()


if __name__ == "__main__":
    main_cmd()

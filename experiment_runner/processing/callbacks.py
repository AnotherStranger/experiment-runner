"""
This module defines usable callbacks
"""

import socket
import sys
from abc import ABC, abstractmethod
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Deque, List, Optional, TextIO, Union

from rich import print  # pylint: disable=redefined-builtin

from experiment_runner.processing.configurator import Configurator
from experiment_runner.processing.mail import Mailer


class Callback(ABC):
    """
    Abstract class for callbacks.
    """

    @abstractmethod
    def on_start(self, command: Union[str, List[str]]) -> None:
        """
        Called when the command starts.
        """
        raise NotImplementedError()

    @abstractmethod
    def on_end(self, command: Union[str, List[str]], returncode: int) -> None:
        """
        Called when the command ends (successfully or not).
        """
        raise NotImplementedError()

    def on_log(self, command, log) -> None:
        """
        Handle a new logline in stdout
        """
        raise NotImplementedError()

    def on_error(self, command: Union[str, List[str]], returncode: int) -> None:
        """
        Called when the command ends with an error. Defaults to on_end.
        """
        self.on_end(command, returncode)

    def on_success(self, command: Union[str, List[str]], returncode: int) -> None:
        """
        Called when the command ends successfully. Defaults to on_end.
        """
        self.on_end(command, returncode)


class MailerCallback(Callback):
    """
    Callback class for sending emails.
    """

    def __init__(self, mailer: Mailer, logging_path: Optional[Path] = None, loglen: int = 100):
        self.mailer = mailer
        self.logging_path = logging_path
        self.log: Deque[str] = deque([], maxlen=loglen)

    @property
    def log_text(self):
        """
        Convert the log queue into a single string
        """
        return "".join(self.log)

    def on_start(self, command: Union[str, List[str]]) -> None:
        """
        Sends an E-Mail on experiment start.
        """
        try:
            self.mailer.send(
                f"{socket.gethostname()}: Experiment started {datetime.now()}",
                f"Experiment started with command:<pre><code>{command}</code></pre>",
            )
        except Exception as err:  # pylint: disable=broad-exception-caught
            print(f"Error while sending an E-Mail. Please check your password/E-Mail config. Error: {err}")
            sys.exit(-1)

    def on_end(self, command: Union[str, List[str]], returncode: int) -> None:
        """
        Do Nothing on end. Specific cases are handled in on_error and on_success
        """

    def on_error(self, command: Union[str, List[str]], returncode: int) -> None:
        """
        Sends an E-Mail on experiment error.
        """
        mail_body = """
        <h1>Error while executing command</h1>
        <p>Command <code>{command}</code> ended with an Error.</p>

        <h2>Log:</h2>
        <pre><code>{log_text}</code></pre>
        """
        self.mailer.send(
            f"{socket.gethostname()}: Experiment ended with error (RC {returncode}). Time: {datetime.now()}",
            mail_body.format(command=command, log_text=self.log_text),
            self.logging_path,
        )

    def on_log(self, command, log) -> None:
        self.log.append(log)

    def on_success(self, command: Union[str, List[str]], returncode: int) -> None:
        """
        Sends an E-Mail on experiment success.
        """
        mail_body = """
        <h1>Command ended successfully</h1>
        <p>Command <code>{command}</code> ended successfully.</p>

        <h2>Log:</h2>
        <pre><code>{log_text}</code></pre>
        """
        self.mailer.send(
            f"{socket.gethostname()}: Experiment ended successfully (RC {returncode}). Time: {datetime.now()}",
            mail_body.format(command=command, log_text=self.log_text),
            self.logging_path,
        )


class LoggerCallback(Callback):
    """
    Callback class for logging.
    """

    file: TextIO

    def __init__(self, file_path: Path):
        self.path: Path = file_path
        self.log_queue: Deque[str] = deque([], maxlen=Configurator().config.logging_buffer_size)

    def on_start(self, command: Union[str, List[str]]) -> None:
        """
        Write command and datetime to log file
        """
        self.write_to_file(
            [
                f"Experiment started {datetime.now()}",
                f"Experiment started with command:<pre><code>{command}</code></pre>",
            ]
        )

    def write_to_file(self, lines: List[str]):
        """
        Open file on given path and write to it
        """
        try:
            with open(self.path, "a", encoding="utf-8") as self.file:
                self.file.writelines(lines)
        except Exception as err:  # pylint: disable=broad-exception-caught
            print(f"Error while writing to log file. Please check your file path. Error: {err}")
            sys.exit(-1)

    def on_end(self, command: Union[str, List[str]], returncode: int) -> None:
        """
        Close file after writing remaining logs
        """
        # Write to file if log is not empty
        if len(self.log_queue) > 0:
            self.write_to_file(list(self.log_queue))
            self.log_queue.clear()

        # Close log file
        if not self.file.closed:
            self.file.close()

    def on_error(self, command: Union[str, List[str]], returncode: int) -> None:
        """
        Nothing to do here
        """

    def on_log(self, command: Union[str, List[str]], log: str) -> None:
        """
        Log everything from stdout and stderr to log or write log to file if log reached maxlen
        """
        # Write to file if log is full
        if not self.log_queue.maxlen or len(self.log_queue) >= self.log_queue.maxlen:
            self.write_to_file(list(self.log_queue))
            self.log_queue.clear()

        # Write in log queue
        self.log_queue.append(log)

    def on_success(self, command: Union[str, List[str]], returncode: int) -> None:
        """
        Nothing to do here
        """

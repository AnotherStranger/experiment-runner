"""
Classes for handling config files
"""

import sys
from pathlib import Path
from typing import Any, Dict

from omegaconf import OmegaConf
from pydantic.dataclasses import dataclass
from rich import print  # pylint: disable=redefined-builtin
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.syntax import Syntax

CONFIG_PATH = Path("~/.config/experiment-runner/config.yml").expanduser()


class ConfiguratorMeta(type):
    """
    Singleton Metaclass for configurator
    """

    _instances: Any = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class ConfigDoesNotExistException(Exception):
    """
    Exception raised when the config file does not exist.
    """


@dataclass
class ConfigurationFile:
    # pylint: disable = R0902
    """
    Configuration file DTO
    """

    # Runner Config
    polling_rate_in_seconds: int = 1

    # Logger Config
    logging_buffer_size: int = 10

    # Mailer Config
    use_mailer: bool = False
    to_email: str = ""
    from_email: str = ""
    host: str = ""
    port: int = 0
    username: str = ""
    password: str = ""

    def dict(self):
        """
        Return object as dict
        """
        return self.model_dump()  # pylint: disable=no-member


class Configurator(metaclass=ConfiguratorMeta):
    """
    Configurator class for handling configurations
    """

    _config: ConfigurationFile = ConfigurationFile()
    config_path: Path

    def __init__(self) -> None:
        self.load_config()

    @property
    def config(self) -> ConfigurationFile:
        """
        Property to get config
        """
        if not self._config:
            print("Config path not defined! Loading default config path.")
            self.load_config()
        return self._config

    def load_config(self, config_path: Path = CONFIG_PATH):
        """
        Load Configuration file from config_path
        """
        self.config_path = config_path

        if not config_path.exists():
            if config_path == CONFIG_PATH:
                self._config = OmegaConf.structured(ConfigurationFile)
                self.save_config()
            else:
                if Confirm.ask(
                    f":warning: It seems there is no config file on {config_path}\nDo you want to create one?"
                ):
                    self._config = self.create_config()
                else:
                    print(
                        "Aborting! Configuration path was defined but no configuration found!"
                    )
                    sys.exit(-1)
        else:
            loaded_config: Any = OmegaConf.to_container(OmegaConf.load(config_path))
            if isinstance(loaded_config, Dict):
                self._config = ConfigurationFile(**loaded_config)
            else:
                raise ValueError("Loaded config is not valid!")

        if self.config.use_mailer and not self.config.password:
            self.config.password = Prompt.ask(
                ":closed_lock_with_key: Password", password=True
            )

            if not self.config.password:
                print("No Password provided. Exiting...")
                sys.exit(-1)

    def create_config(self) -> ConfigurationFile:
        """
        Creates a new ConfigurationFile interactively
        """
        if self.config_path.exists() and not Confirm.ask(
            ":warning: The config does already exist. Recreate it? :warning:"
        ):
            loaded_config: Any = OmegaConf.to_container(
                OmegaConf.load(self.config_path)
            )
            if isinstance(loaded_config, Dict):
                return ConfigurationFile(**loaded_config)
            raise ValueError("Loaded config is not valid!")

        self._config: ConfigurationFile = OmegaConf.structured(ConfigurationFile)
        print(
            "This config fully supports Omegaconf syntax. See: https://omegaconf.readthedocs.io/"
        )
        print("--------- Mailer Configuration ------------")

        if Confirm.ask("Do you want to configure an email-address for the mailer?"):
            self.config.use_mailer = True
            self.config.to_email = Prompt.ask(":e-mail: Who should receive the email?")
            self.config.from_email = Prompt.ask(":e-mail: Your email address")
            self.config.host = Prompt.ask(":globe_with_meridians: SMTP host")
            self.config.port = IntPrompt.ask(":100: SMTP port", default=587)
            self.config.username = Prompt.ask(":bust_in_silhouette: Username")
            self.config.password = Prompt.ask(
                ":closed_lock_with_key: Password (The system will ask, if left empty)",
                password=True,
                default="",
            )

        show_config = Confirm.ask(
            "Show config? :warning: WARNING: your passphrase will be visible! :warning:",
            default=False,
        )

        if show_config:
            print(Syntax(OmegaConf.to_yaml(self.config).strip(), "yaml"))

        should_save = Confirm.ask(
            "Save config? Otherwise it will be used for this run only.", default=True
        )

        if should_save:
            self.save_config()

        return ConfigurationFile(**self.config.dict())

    def save_config(self):
        """
        Save config file
        """
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with self.config_path.open("w", encoding="utf8") as fp_conf:
            OmegaConf.save(self.config, fp_conf)
        self.config_path.chmod(0o600)

    def show_config(self):
        """
        Prints out config parameters from config_path
        """
        if not self.config:
            raise ConfigDoesNotExistException("No config file found!")

        print(
            f"Location: {self.config_path}\n",
            "------- Mailer Configuration --------\n",
            f"Use-mailer: {self.config.use_mailer}\n",
            f"From_mail: {self.config.from_email}\n",
            f"To_mail: {self.config.to_email}\n",
            f"Host: {self.config.host}\n",
            f"Port: {self.config.port}\n",
            f"Username: {self.config.username}\n",
            f"Password: {self.config.password}\n",
            "------- Other Configurations -------\n",
            f"Polling_rate_in_seconds: {self.config.polling_rate_in_seconds}\n",
            f"Logging_buffer_size: {self.config.logging_buffer_size}\n",
        )

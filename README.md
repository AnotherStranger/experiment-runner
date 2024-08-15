# Experiment Runner
<!-- markdownlint-disable -->
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-4-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->
<!-- markdownlint-restore -->

Experiment Runner is a command-line interface (CLI) application that helps you manage and run experiments.

## Usage

### Commands

#### create-config

`experiment create-config [OPTIONS]`

Create or edit the configuration file.

* `--config-path PATH`: Specify the path to the configuration file.
* `--help`: Show help message and exit.

Example:

```bash
experiment create-config --config-path /path/to/config.yml
```

#### gpu-info

`experiment gpu-info [OPTIONS]`

Print current GPU utilization information.

* `--attributes ATTRIBUTES`: Specify which attributes to display (e.g., memory, temperature).
* `--help`: Show help message and exit.

Example:

```bash
experiment gpu-info --attributes memory,temperature
```

#### gpu-usage-report

`experiment gpu-usage-report`

Print a report of GPU usage over time.

No options available.

Example:

```bash
experiment gpu-usage-report
```

#### print-gpus-env

`experiment print-gpus-env [OPTIONS]`

Print environment variables related to GPUs.

* `--help`: Show help message and exit.

Example:

```bash
experiment print-gpus-env
```

#### run

`experiment run [COMMAND] [OPTIONS]`

Run an experiment with the specified command.

* `command TEXT`: The command to execute.
* `--gpu-selection STRATEGY`: Specify the GPU selection strategy (e.g., first, last, random).
* `--num-gpus INTEGER`: Specify the number of GPUs to use.
* `--send-mail`/`--no-send-mail`: Send an email after the experiment finishes or fails.
* `--wait-for-gpus`/`--no-wait-for-gpus`: Wait until the specified number of GPUs are available.
* `--logging PATH`: Write output to a file at the specified location.
* `--config-path PATH`: Use the specified configuration file.

Example:

```bash
experiment run "python my_experiment.py" --gpu-selection first --num-gpus 2 --send-mail --wait-for-gpus
```

#### show-config

`experiment show-config [OPTIONS]`

Display the current configuration settings.

* `--config-path PATH`: Specify the path to the configuration file.
* `--help`: Show help message and exit.

Example:

```bash
experiment show-config --config-path /path/to/config.yml
```

#### test-mail

`experiment test-mail SUBJECT MESSAGE [OPTIONS]`

Send a test email using the mailer.

* `subject TEXT`: The subject of the email.
* `message TEXT`: The body of the email.
* `--config-path PATH`: Specify the path to the configuration file.
* `--help`: Show help message and exit.

Example:

```bash
experiment test-mail "Test Email" "This is a test email." --config-path /path/to/config.yml
```

#### version

`experiment version`

Display the version of Experiment Runner.

No options available.

Example:

```bash
experiment version
```

Note: This guide provides an overview of the available commands and options. For more detailed information, use the `--help` option with each command.

## Development Setup

TLDR; run

```bash
source ./dev-setup.sh
```

and you should be ready to go!

## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/AnotherStranger"><img src="https://avatars.githubusercontent.com/u/6563442?v=4?s=100" width="100px;" alt="Anotherstranger"/><br /><sub><b>Anotherstranger</b></sub></a><br /><a href="https://github.com/AnotherStranger/experiment-runner/commits?author=AnotherStranger" title="Code">💻</a> <a href="https://github.com/AnotherStranger/experiment-runner/commits?author=AnotherStranger" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/tomvonwirth"><img src="https://avatars.githubusercontent.com/u/155973942?v=4?s=100" width="100px;" alt="tomvonwirth"/><br /><sub><b>tomvonwirth</b></sub></a><br /><a href="https://github.com/AnotherStranger/experiment-runner/commits?author=tomvonwirth" title="Code">💻</a> <a href="https://github.com/AnotherStranger/experiment-runner/commits?author=tomvonwirth" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/philipp-kohl"><img src="https://avatars.githubusercontent.com/u/82207307?v=4?s=100" width="100px;" alt="Philipp Kohl"/><br /><sub><b>Philipp Kohl</b></sub></a><br /><a href="https://github.com/AnotherStranger/experiment-runner/commits?author=philipp-kohl" title="Code">💻</a> <a href="https://github.com/AnotherStranger/experiment-runner/commits?author=philipp-kohl" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/levithas"><img src="https://avatars.githubusercontent.com/u/95447711?v=4?s=100" width="100px;" alt="levithas"/><br /><sub><b>levithas</b></sub></a><br /><a href="https://github.com/AnotherStranger/experiment-runner/commits?author=levithas" title="Code">💻</a> <a href="https://github.com/AnotherStranger/experiment-runner/commits?author=levithas" title="Documentation">📖</a></td>
    </tr>
  </tbody>
  <tfoot>
    <tr>
      <td align="center" size="13px" colspan="7">
        <img src="https://raw.githubusercontent.com/all-contributors/all-contributors-cli/1b8533af435da9854653492b1327a23a4dbd0a10/assets/logo-small.svg">
        <a href="https://all-contributors.js.org/docs/en/bot/usage">Add your contributions</a>
        </img>
      </td>
    </tr>
  </tfoot>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

<!-- markdownlint-disable -->
This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!
<!-- markdownlint-restore -->

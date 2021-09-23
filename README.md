<p align="center">
  <img src="https://raw.githubusercontent.com/unikubehq/cli/main/logo_cli.png" width="400">
</p>
<p align="center">
    <img alt="Build Status" src="https://github.com/unikubehq/cli/actions/workflows/python-app.yaml/badge.svg">
    <a href="https://sonarcloud.io/dashboard?id=unikubehq_cli"><img alt="Quality Gate Status" src="https://sonarcloud.io/api/project_badges/measure?project=unikubehq_cli&metric=alert_status"></a>
    <a href="https://coveralls.io/github/unikubehq/cli?branch=main"><img alt="Coverage Status" src="https://coveralls.io/repos/github/unikubehq/cli/badge.svg?branch=main"></a>
    <a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

# The Unikube CLI

This is the command line interface for [unikube][link_unikube].

## Documentation

The unikube [cli documentation][link_unikube_cli_documentation] is automatically built.

### Installation

#### General

The unikube cli can be installed via `pip`. Please make sure you are using Python 3.

```shell
pip install unikube
```

#### MacOS

The unikube cli is also installable via brew:

```shell
brew tap unikubehq/tooling
brew install unikubehq/tooling/unikube
```

### Make Local

```bash
cd docs
make html
```

## Development

---

### Setup

Start the local unikube development cluster:

```bash
k3d cluster start unikube
```

### Install CLI

To install the latest (pre-)release of the Unikube CLI type

```bash
sudo pip3 install unikube==<VERSION> --upgrade --pre
```

### Virtual Environment + Requirements

Create virtual environment:

```bash
python -m .venv venv
```

Install requirements (production + development):

```bash
pip3 install -r requirements.txt -r requirements.dev.txt
```

### Version Build + Release

Version management is handled via bump2version.

`bump2version patch|minor|major`

Increase _dev_ version (e.g.: 1.0.0-dev1 -> 1.0.0-dev2):

`bump2version build`

Create release (e.g.: 1.0.0-dev2 -> 1.0.0):

`bump2version release`

## Test

---

Tests for the unikube cli are developed using the `pytest` framework in combination with the _click.testing_ module.

Thus, it is possible to run the tests using `pytest` or by configuring the testing environment/options within your IDE to use `pytest`.

Currently, most tests are developed directly against the unikube API, using a test-account. Therefore, it is required to provide the credentials via the following environment variables:

```
TESTRUNNER_EMAIL=...
TESTRUNNER_SECRET=...
```

Otherwise, tests might fail locally, even if they are correct.

It is possible to set the environment variables using an `.env` file within your virtual environment or by providing them explicitly:

```
TESTRUNNER_EMAIL=... TESTRUNNER_SECRET=... pytest
```

[link_unikube]: https://unikube.io
[link_unikube_cli_documentation]: https://cli.unikube.io

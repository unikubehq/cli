![Unikube Logo](https://raw.githubusercontent.com/unikubehq/cli/main/docs/_static/img/Unikube-Logo-H-NoShadow.svg)


# The Unikube CLI

This is the command line interface for [unikube][link_unikube].

--------------------------------------------------------------------------------
![Build Status](https://github.com/unikubehq/cli/actions/workflows/python-app.yaml/badge.svg)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=unikubehq_cli&metric=alert_status)](https://sonarcloud.io/dashboard?id=unikubehq_cli)
[![Coverage Status](https://coveralls.io/repos/github/unikubehq/cli/badge.svg?branch=main)](https://coveralls.io/github/unikubehq/cli?branch=main)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Documentation

---

The unikube [cli documentation][link_unikube_cli_documentation] is automatically built.

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

TODO

[link_unikube]: https://unikube.io
[link_unikube_cli_documentation]: https://cli.unikube.io

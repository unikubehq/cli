# Unikube CLI

This is the CLI for [unikube][link_unikube].

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

```bash
sudo pip3 install unikube==<VERSION> --upgrade
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

[link_unikube]: unikube.io
[link_unikube_cli_documentation]: cli.unikube.io

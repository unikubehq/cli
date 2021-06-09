# -*- coding: utf-8 -*-
import os
import platform
import re
import subprocess
from time import sleep
from typing import Dict, List, Optional, Tuple

import click
import semantic_version

import src.cli.console as console
from src import settings


class LocalDependency(object):
    """
    This is a local development dependency unikube
    """

    cmd = None
    verbose_name = None
    required = None
    required_version = None

    def probe(self, silent) -> Tuple[bool, str]:
        console.info(self.check_message(), silent=silent, nl=False)

        if not self.required_version:
            try:
                kwargs = {
                    "stdout": open(os.devnull, "w"),
                    "close_fds": True,
                    "stderr": subprocess.STDOUT,
                }
                subprocess.check_call(self.cmd, **kwargs)
                self._click_echo(" Ok", silent=silent, fg="green")
                return True, ""
            except (subprocess.CalledProcessError, FileNotFoundError):
                self._click_echo(" Error", silent=silent, fg="red")
                return False, self.notfound_message()
        else:
            try:
                pout = subprocess.run(self.cmd, capture_output=True, encoding="UTF-8")
            except (subprocess.CalledProcessError, FileNotFoundError):
                self._click_echo(" Error", silent=silent, fg="red")
                return False, self.notfound_message()
            else:
                cmd_version = self.prepare_version_string(pout.stdout)
                version, sufficient = self.check_version(cmd_version)
                if version and sufficient:
                    self._click_echo(f" Ok (Version {version})", silent=silent, fg="green")
                    return True, ""
                elif version:
                    self._click_echo(f" Error (Version {version})", silent=silent, fg="red")
                    return False, self.oldversion_message()
                else:
                    self._click_echo(" Error", silent=silent, fg="red")
                    return False, self.notfound_message()

    def _click_echo(self, msg, silent=False, fg=""):
        if not silent:
            click.secho(msg, fg=fg)

    def install(self) -> int:
        return_code = 0
        for idx, step in enumerate(self.installation_steps):
            console.info(f"Running installation step #{idx+1}: {step}")
            try:
                process = subprocess.run(step, shell=True)
                return_code += process.returncode
            except Exception as cpr:
                console.error(f"An error occured during the installation of {self.verbose_name}:")
                console.error(str(cpr))
                return 1
        return return_code

    def notfound_message(self) -> str:
        return f"Please make sure that '{self.verbose_name}' is correctly installed on your computer."

    def oldversion_message(self) -> str:
        return f"The version of '{self.verbose_name}' on your computer is too old."

    def check_message(self) -> str:
        return f"Checking {self.verbose_name} "

    def check_version(self, cmd_version) -> Tuple[str, bool]:
        self.installed_version = semantic_version.Version(cmd_version)
        required_version = semantic_version.Version(self.required_version)
        if required_version <= self.installed_version:
            return str(self.installed_version), True
        else:
            return str(self.installed_version), False

    def prepare_version_string(self, cmd_version) -> str:
        return cmd_version.strip()


class Kubectl(LocalDependency):
    cmd = ("kubectl", "version", "--client")
    verbose_name = "Kubectl"
    required_version = settings.KUBECTL_MIN_CLI_VERSION

    @property
    def installation_steps(self):
        # Check for OS
        if platform.system() == "Darwin":
            return [
                "curl -LO https://storage.googleapis.com/kubernetes-release/release/$"
                "(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)"
                "/bin/darwin/amd64/kubectl",
                "chmod +x ./kubectl",
                "sudo mv ./kubectl /usr/local/bin/kubectl",
            ]

        return [
            "curl -LO https://storage.googleapis.com/kubernetes-release/release/$"
            "(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)"
            "/bin/linux/amd64/kubectl",
            "chmod +x ./kubectl",
            "sudo mv ./kubectl /usr/local/bin/kubectl",
        ]

    def prepare_version_string(self, cmd_version) -> str:
        # version.Info{Major:"1", Minor:"19", GitVersion:"v1.19.0", GitCommit:"e19964183377d0ec2052d1f1fa930c4d7575bd50"
        # , GitTreeState:"clean", BuildDate:"2020-08-26T14:30:33Z", GoVersion:"go1.15",
        # Compiler:"gc", Platform:"linux/amd64"}

        match = re.search(r'GitVersion:"(.+?)"', cmd_version).group(1)
        return match.strip("v")


class K3s(LocalDependency):
    cmd = ("k3s", "--version")
    verbose_name = "K3S"
    required_version = settings.K3S_CLI_MIN_VERSION

    def prepare_version_string(self, cmd_version) -> str:
        # k3s version vx.yy.z+k3s1 (12345678)
        return cmd_version.replace("k3s version ", "").replace("v", "").split(" ")[0]

    @property
    def installation_steps(self):
        # Check for OS
        if platform.system() == "Darwin":
            return ["curl -sfL https://get.k3s.io | sh -"]
        return ["curl -sfL https://get.k3s.io | sudo bash"]


class K3d(LocalDependency):
    cmd = ("k3d", "--version")
    verbose_name = "k3d"
    website = settings.K3D_WEBSITE
    required_version = settings.K3D_CLI_MIN_VERSION
    installation_steps = ["curl -s https://raw.githubusercontent.com/rancher/k3d/main/install.sh | sudo bash"]

    def prepare_version_string(self, cmd_version) -> str:
        # k3d version vx.y.z
        # k3s version v1.18.6-k3s1 (default)
        return cmd_version.split("\n")[0].replace("k3d version ", "").replace("v", "").split(" ")[0]


class DockerEngine(LocalDependency):
    cmd = ("docker", "run", "--rm", settings.DOCKER_TEST_IMAGE, "true")
    verbose_name = "Docker Engine"


class Docker(LocalDependency):
    cmd = ("docker", "--version")
    verbose_name = "Docker"
    required_version = settings.DOCKER_CLI_MIN_VERSION
    website = settings.DOCKER_WEBSITE

    def prepare_version_string(self, cmd_version) -> str:
        # Docker version xx.yy.z, build 1234567
        cmd_version = cmd_version.replace("Docker version ", "").split(",")[0]
        # Docker uses a slightly incorrect semantic versioning:
        # e.g. Docker version 19.03.8, build afacb8b7f0 -> ValueError: Invalid leading zero in minor: '19.03.8'
        cmd_version = ".".join(str(int(bit)) for bit in cmd_version.split("."))
        return cmd_version


class Telepresence(LocalDependency):
    cmd = ("telepresence", "--version")
    verbose_name = "Telepresence"
    required_version = settings.TELEPRESENCE_CLI_MIN_VERSION

    @property
    def installation_steps(self):
        if platform.system() == "Darwin":
            return [
                "brew cask install osxfuse",
                "brew install datawire/blackbird/telepresence",
            ]
        return [
            "curl -s https://packagecloud.io/install/repositories/datawireio/telepresence/script.deb.sh | sudo bash",
            "sudo apt install -y --no-install-recommends telepresence",
        ]

    def check_version(self, cmd_version) -> Tuple[str, bool]:
        # Telepresence does not support SemVer
        self.installed_version = re.sub(r"[^0-9\.]", "", cmd_version)
        self.required_version = re.sub(r"[^0-9\.]", "", self.required_version)
        required_major, required_minor = map(int, self.required_version.split(".")[0:2])
        installed_major, installed_minor = map(int, self.installed_version.split(".")[0:2])
        # simple check for major and minor version
        if installed_major > required_major:
            return str(self.installed_version), True
        elif installed_major >= required_major and installed_minor >= required_minor:
            return str(self.installed_version), True
        else:
            return str(self.installed_version), False


class Homebrew(LocalDependency):
    cmd = ("brew", "--version")
    verbose_name = "Homebrew"
    required_version = settings.HOMEBREW_CLI_VERSION
    installation_steps = [
        "/bin/bash -c $(curl -fsSL " "https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
    ]
    website = settings.HOMEBREW_WEBSITE

    def prepare_version_string(self, cmd_version) -> str:
        return cmd_version.split("\n")[0].replace("Homebrew ", "")


ALL_DEPENDENCIES = [
    Docker,
    DockerEngine,
    Kubectl,
    K3d,
    Telepresence,
]

if platform.system() == "Darwin":
    ALL_DEPENDENCIES = [Homebrew] + ALL_DEPENDENCIES


def probe_dependencies(silent=False) -> List[Dict[str, str]]:
    """Generates a report of the required software and versions"""
    results = []
    for klass in ALL_DEPENDENCIES:
        check = klass()
        success, msg = check.probe(silent=silent)
        if check.required_version:
            required_version = check.required_version
            if success:
                installed_version = check.installed_version
            else:
                installed_version = ""
        else:
            required_version = ""
            installed_version = ""
        results.append(
            {
                "name": check.verbose_name,
                "success": success,
                "msg": msg,
                "required_version": required_version,
                "installed_version": installed_version,
            }
        )
    return results


def install_dependency(name, silent=False) -> Optional[int]:
    try:
        klass = next(
            filter(
                lambda klass: klass.verbose_name.lower() == name.lower(),
                ALL_DEPENDENCIES,
            )
        )
    except StopIteration:
        console.error(f"The dependency name '{name}' is not valid. No action taken.")
        return None
    else:
        if hasattr(klass, "installation_steps"):
            console.info(f"Now running installation setup for {klass.verbose_name}")
            rcode = klass().install()
            if rcode == 0:
                console.success(f"The installation of {klass.verbose_name} was successful.")
            else:
                console.error(f"The installation of {klass.verbose_name} was not successful.")
            return rcode
        else:
            console.error(
                f"The unikube.tech CLI does currently not support the installation of {klass.verbose_name}. "
                f"{'Please find instructions here: ' + klass.website if hasattr(klass, 'website') else ''}"
            )
            return None

# -*- coding: utf-8 -*-
import platform
import re
import subprocess
from time import sleep, time
from typing import List

from pydantic import BaseModel

import unikube.cli.console as console
from unikube.cluster.bridge.bridge import AbstractBridge
from unikube.cluster.system import KubeAPI, KubeCtl


class TelepresenceData(BaseModel):
    pass


class Telepresence(AbstractBridge, KubeCtl):
    base_command = "telepresence"

    def intercept_count(self) -> int:
        arguments = ["status"]
        process = self._execute(arguments)
        status = process.stdout.readlines()

        # parse intercept count
        try:
            intercept_line = status[15]
            match = re.findall("[ ]{1,}Intercepts[ ]{1,}:(.*)[ ]{1,}total", intercept_line)
            intercept_count = int(match[0])
        except Exception as e:
            console.debug(e)
            intercept_count = 0

        return intercept_count

    def pre_cluster_up(self):
        pass

    def post_cluster_up(self):
        console.info("Now connecting Telepresence daemon. You probably have to enter your 'sudo' password.")
        k8s = KubeAPI(self._kubeconfig_path)
        timeout = time() + 60  # wait one minute
        while not k8s.is_available or time() > timeout:
            sleep(1)

        if not k8s.is_available:
            console.error(
                "There was an error bringing up the project cluster. The API was not available within the"
                "expiration period.",
                _exit=True,
            )

        self.start()

    def pre_cluster_down(self):
        self.stop()

    def post_cluster_down(self):
        pass

    def _execute_intercept(self, arguments) -> subprocess.Popen:
        cmd = [self.base_command] + arguments
        kwargs = self._get_kwargs()
        process = subprocess.Popen(cmd, **kwargs)
        for stdout_line in iter(process.stdout.readline, ""):
            print(stdout_line, end="", flush=True)
        return process

    def swap(self, deployment, image_name, command=None, namespace=None, envs=None, mounts=None, port=None):
        arguments = ["intercept", "--no-report", deployment]
        if namespace:
            arguments = arguments + ["--namespace", namespace]

        arguments = arguments + ["--port", f"{port}:{port}", "--docker-run", "--"]
        if platform.system() != "Darwin":
            arguments.append("--network=host")
        arguments += [
            f"--dns-search={namespace}",
            "--rm",
        ]
        if mounts:
            for mount in mounts:
                arguments = arguments + ["-v", f"{mount[0]}:{mount[1]}"]
        if envs:
            for env in envs:
                arguments = arguments + ["--env", f"{env[0]}={env[1]}"]

        # this name to be retrieved for "app shell" command
        arguments = arguments + ["--name", image_name.replace(":", "")]
        arguments.append(image_name)
        if command:
            arguments = arguments + ["sh", "-c"] + [f"{' '.join(command)}"]

        console.debug(arguments)
        try:
            process = self._execute_intercept(arguments)
            if process.returncode and (process.returncode != 0 and not process.returncode != 137):
                console.error(
                    "There was an error with switching the deployment, please find details above", _exit=False
                )
        except KeyboardInterrupt:
            pass
        console.info("Stopping the switch operation. It takes a few seconds to reset the cluster.")
        self.leave(deployment, namespace, silent=True)
        self.uninstall(deployment, namespace, silent=True)

    def leave(self, deployment, namespace=None, silent=False):
        arguments = ["leave", "--no-report"]
        if namespace:
            arguments.append(f"{deployment}-{namespace}")
        else:
            arguments.append(deployment)
        console.debug(arguments)
        process = self._execute(arguments)
        if not silent and process.returncode and process.returncode != 0:
            console.error("There was an error with leaving the deployment, please find details above", _exit=False)

    def uninstall(self, deployment, namespace=None, silent=False):
        arguments = ["uninstall", "--agent", deployment]
        arguments.append(deployment)
        if namespace:
            arguments += ["-n", namespace]
        console.debug(arguments)
        process = self._execute(arguments)
        if not silent and process.returncode and process.returncode != 0:
            console.error(
                "There was an error with uninstalling the traffic agent, please find details above", _exit=False
            )

    def _get_environment(self):
        env = super(Telepresence, self)._get_environment()
        return env

    def start(self) -> None:
        arguments = ["connect", "--no-report"]
        process = self._execute(arguments)
        if process.returncode and process.returncode != 0:
            # this is a retry
            process = self._execute(arguments)
            if process.returncode and process.returncode != 0:
                console.error(f"Could not start Telepresence daemon: {process.stdout.readlines()}", _exit=False)

    def stop(self) -> None:
        arguments = ["quit", "--no-report"]
        process = self._execute(arguments)
        if process.returncode and process.returncode != 0:
            console.error("Could not stop Telepresence daemon", _exit=False)

    def list(self, namespace=None, flat=False) -> List[str]:
        arguments = ["list", "--no-report"]
        if namespace:
            arguments += ["--namespace", namespace]
        process = self._execute(arguments)
        deployment_list = process.stdout.readlines()
        result = []
        if deployment_list:
            for deployment in deployment_list:
                try:
                    name, status = map(str.strip, deployment.split(":"))
                except ValueError:
                    continue
                if name in ["Intercept name", "State", "Workload kind", "Destination", "Intercepting"]:
                    continue
                if "intercepted" in status:
                    result.append((name, "intercepted"))
                else:
                    result.append((name, "ready"))
        if flat:
            result = [deployment[0] for deployment in result]
        return result

    def is_swapped(self, deployment, namespace=None) -> bool:
        deployments = self.list(namespace)
        swapped = any(filter(lambda x: x[0] == deployment and x[1] == "intercepted", deployments))
        return swapped


class TelepresenceBuilder:
    def __call__(
        self,
        kubeconfig_path: str,
        **kwargs,
    ):
        instance = Telepresence(kubeconfig_path=kubeconfig_path)
        return instance

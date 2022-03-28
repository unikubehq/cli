# -*- coding: utf-8 -*-
import platform
import re
import subprocess
import tempfile
from time import sleep, time
from typing import List, Tuple

from pydantic import BaseModel

import unikube.cli.console as console
from unikube import settings
from unikube.cluster.bridge.bridge import AbstractBridge
from unikube.cluster.system import Docker, KubeAPI, KubeCtl
from unikube.unikubefile.unikube_file_1_0 import UnikubeFileApp


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

    def pre_cluster_up(self) -> bool:
        return True

    def post_cluster_up(self) -> bool:
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

        # start
        arguments = ["connect", "--no-report"]
        process = self._execute(arguments)
        if process.returncode and process.returncode != 0:
            # this is a retry
            process = self._execute(arguments)
            if process.returncode and process.returncode != 0:
                console.error(f"Could not start Telepresence daemon: {process.stdout.readlines()}", _exit=False)

        return True

    def pre_cluster_down(self) -> bool:
        arguments = ["quit", "--no-report"]
        process = self._execute(arguments)
        if process.returncode and process.returncode != 0:
            console.error("Could not stop Telepresence daemon", _exit=False)

        return True

    def post_cluster_down(self) -> bool:
        return True

    def _execute_intercept(self, arguments) -> subprocess.Popen:
        cmd = [self.base_command] + arguments
        kwargs = self._get_kwargs()
        process = subprocess.Popen(cmd, **kwargs)
        for stdout_line in iter(process.stdout.readline, ""):
            print(stdout_line, end="", flush=True)
        return process

    def __service_account_tokens(self, kubeconfig_path: str, namespace: str, deployment: str, volumes: list):
        k8s = KubeAPI(kubeconfig_path=kubeconfig_path, namespace=namespace)
        service_account_tokens = k8s.get_serviceaccount_tokens(deployment)

        if service_account_tokens:
            tmp_sa_token = tempfile.NamedTemporaryFile(delete=True)
            tmp_sa_cert = tempfile.NamedTemporaryFile(delete=True)
            tmp_sa_token.write(service_account_tokens[0].encode())
            tmp_sa_cert.write(service_account_tokens[1].encode())
            tmp_sa_token.flush()
            tmp_sa_cert.flush()
            volumes.append(f"{tmp_sa_token.name}:{settings.SERVICE_TOKEN_FILENAME}")
            volumes.append(f"{tmp_sa_cert.name}:{settings.SERVICE_CERT_FILENAME}")
        else:
            tmp_sa_token = None
            tmp_sa_cert = None

        return volumes, tmp_sa_token, tmp_sa_cert

    def switch(
        self,
        kubeconfig_path: str,
        deployment: str,
        namespace: str,
        ports: List[str],
        unikube_file_app: UnikubeFileApp,
        *args,
        **kwargs,
    ):
        # arguments
        port = self._get_intercept_port(unikube_file_app=unikube_file_app, ports=ports)
        console.debug(f"port: {port}")

        env = unikube_file_app.get_environment()
        console.debug(f"env: {env}")

        command = unikube_file_app.get_command(port=port)
        command = " ".join(command)
        console.debug(f"command: {command}")

        volumes = [":".join(item) for item in unikube_file_app.get_mounts()]
        console.debug(f"volumes: {volumes}")

        env = ["=".join(item) for item in unikube_file_app.get_environment()]
        console.debug(f"env: {env}")

        # service account tokens
        volumes, tmp_sa_token, tmp_sa_cert = self.__service_account_tokens(
            kubeconfig_path=kubeconfig_path, namespace=namespace, deployment=deployment, volumes=volumes
        )

        # telepresence
        arguments = ["intercept", "--no-report", deployment]
        if namespace:
            arguments += ["--namespace", namespace]

        arguments += ["--port", f"{port}:{port}", "--docker-run", "--"]
        if platform.system() != "Darwin":
            arguments.append("--network=host")

        arguments += [
            f"--dns-search={namespace}",
            "--rm",
        ]

        if volumes:
            for volume in volumes:
                arguments += ["-v", volume]

        if env:
            for e in env:
                arguments += ["--env", f"{e[0]}={e[1]}"]

        # this name to be retrieved for "app shell" command
        image_name = self.get_docker_image_name(deployment=deployment)
        arguments += ["--name", image_name.replace(":", "")]
        arguments.append(image_name)
        if command:
            arguments += ["sh", "-c"] + [f"{' '.join(command)}"]

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
        self.kill_switch(deployment=deployment, namespace=namespace)

        # service account tokens
        if tmp_sa_token:
            tmp_sa_token.close()
            tmp_sa_cert.close()

    def is_switched(self, deployment, namespace=None) -> bool:
        deployments = self.__get_deployments(namespace)
        swapped = any(filter(lambda x: x[0] == deployment and x[1] == "intercepted", deployments))
        return swapped

    def kill_switch(self, deployment: str, namespace: str) -> bool:
        # leave
        arguments = ["leave", "--no-report"]
        if namespace:
            arguments.append(f"{deployment}-{namespace}")
        else:
            arguments.append(deployment)

        console.debug(arguments)
        process = self._execute(arguments)
        if process.returncode and process.returncode != 0:
            console.error("There was an error with leaving the deployment, please find details above", _exit=False)

        # uninstall
        arguments = ["uninstall", "--agent", deployment]
        arguments.append(deployment)
        if namespace:
            arguments += ["-n", namespace]

        console.debug(arguments)
        process = self._execute(arguments)
        if process.returncode and process.returncode != 0:
            console.error(
                "There was an error with uninstalling the traffic agent, please find details above", _exit=False
            )

        # docker
        image_name = self.get_docker_image_name(deployment=deployment)
        docker = Docker()
        if docker.check_running(image_name):
            docker.kill(name=image_name)

    def __get_deployments(self, namespace=None, flat=False) -> List[str]:
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


class TelepresenceBuilder:
    def __call__(
        self,
        kubeconfig_path: str,
        **kwargs,
    ):
        instance = Telepresence(kubeconfig_path=kubeconfig_path)
        return instance

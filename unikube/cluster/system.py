# -*- coding: utf-8 -*-
import os
import subprocess
from pathlib import Path
from typing import List, Tuple

import click
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream
from urllib3.exceptions import MaxRetryError

import unikube.cli.console as console
from unikube import settings


class UnikubeClusterUnavailableError(Exception):
    pass


class CMDWrapper(object):
    base_command = None

    class CMDException(Exception):
        pass

    def __init__(self, debug_output=False):
        self._debug_output = debug_output

    def _execute(self, arguments, stdin: str = None, print_output: bool = False) -> subprocess.Popen:
        cmd = [self.base_command] + arguments
        kwargs = self._get_kwargs()
        process = subprocess.Popen(cmd, **kwargs)
        if stdin:
            process.communicate(stdin)
        try:
            if print_output:
                for stdout_line in iter(process.stdout.readline, ""):
                    print(stdout_line, end="", flush=True)
            process.wait()
        except KeyboardInterrupt:
            try:
                process.terminate()
            except OSError:
                pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
        return process

    def _run(self, arguments) -> subprocess.CompletedProcess:
        cmd = [self.base_command] + arguments
        return subprocess.run(cmd, env=self._get_environment())

    def _get_kwargs(self):
        kwargs = {"env": self._get_environment(), "encoding": "utf-8"}
        if not self._debug_output:
            kwargs.update(
                {
                    "stdout": subprocess.PIPE,
                    "close_fds": True,
                    "stderr": subprocess.STDOUT,
                }
            )
        return kwargs

    def _get_environment(self):
        env = os.environ.copy()
        return env


class KubeCtl(CMDWrapper):
    base_command = "kubectl"

    def __init__(self, kubeconfig_path: str, debug_output: bool = False):
        if not kubeconfig_path:
            raise ValueError("Project does not contain the kubeconfigPath parameter")
        self._kubeconfig_path = kubeconfig_path
        super(KubeCtl, self).__init__(debug_output)

    def _get_environment(self):
        env = super(KubeCtl, self)._get_environment()
        env["KUBECONFIG"] = self._kubeconfig_path
        return env

    def _get_kwargs(self):
        kwargs = super(KubeCtl, self)._get_kwargs()
        kwargs["stdin"] = subprocess.PIPE
        return kwargs

    def create_namespace(self, namespace: str):
        arguments = ["create", "namespace", namespace]
        self._execute(arguments)

    def apply_str(self, namespace, text: str):
        arguments = ["apply", "--namespace", namespace, "-f", "-"]
        self._execute(arguments, text)

    def delete_str(self, namespace, text: str):
        arguments = ["delete", "--namespace", namespace, "-f", "-"]
        self._execute(arguments, text)

    def get_pods(self, namespace):
        arguments = ["get", "pods", "--namespace", namespace]
        process = self._execute(arguments)
        output = process.stdout.read()
        return output

    def describe_pod(self, pod, namespace):
        arguments = ["describe", "pod", pod, "--namespace", namespace]
        process = self._execute(arguments)
        output = process.stdout.read()
        return output

    def exec_pod(self, pod, namespace, command, interactive=False, container=None):
        arguments = ["exec", "-it", pod]

        if namespace:
            arguments += ["--namespace", namespace]

        if container:
            arguments += ["--container", container]

        arguments += ["--", command]
        if interactive:
            console.info(f"Running '{command}' (interactively) on: {pod}. Please press Ctrl+D to exit.")
            process = self._run(arguments)
            output = process.stdout
        else:
            process = self._execute(arguments)
            output = process.stdout.read()
        return output


class Docker(CMDWrapper):
    base_command = "docker"

    def build(self, tag, context, dockerfile=None, target=None) -> Tuple[bool, str]:
        arguments = ["build", "-t", tag, context]
        if target:
            arguments = arguments + ["--target", target]

        if dockerfile:
            arguments = arguments + ["-f", dockerfile]

        process = self._execute(arguments)

        if process.returncode == 0:
            return True, ""
        else:
            return (
                False,
                "Could not build the Docker image, please make sure the image can be built",
            )

    def check_running(self, name) -> bool:
        """Checks whether an image or a specific container is running."""
        arguments = ["ps"]
        process = self._execute(arguments)
        output = process.stdout.read()
        return name in output

    def daemon_active(self):
        """Checks whether docker daemon is running.

        Based on docker documentation (https://docs.docker.com/config/daemon/#check-whether-docker-is-running).
        `docker info` exists with non-zero exit code when docker is not running.
        """
        arguments = ["info"]
        process = self._execute(arguments)
        return process.returncode == 0

    def exec(self, container, command, interactive=False):
        arguments = ["exec", "-it", container, command]
        if interactive:
            console.info(f"Running '{command}' (interactively) on: {container}. Please press Ctrl+D to exit.")
            process = self._run(arguments)
            output = process.stdout
        else:
            process = self._execute(arguments)
            output = process.stdout.read()
        return output

    def kill(self, _id=None, name=None):
        if _id:
            pass
        elif name:
            _id = self.get_container_id(name)
        arguments = ["kill", _id]
        self._execute(arguments)

    def get_container_id(self, name):
        arguments = ["ps", "-aq", "--filter", f"ancestor={name}"]
        process = self._execute(arguments)
        output = process.stdout.read()
        return output.strip()

    def image_exists(self, name):
        arguments = ["images", "-q", name]
        process = self._execute(arguments)
        output = process.stdout.read()
        if output.strip():
            return True
        else:
            return False


class KubeAPI(object):
    def __init__(self, kubeconfig_path: str, namespace: str = None, deck=None):
        file = Path(kubeconfig_path)
        if not file.is_file():
            raise Exception(f"kubeconfig does not exist: {kubeconfig_path}")

        self._kubeconfig_path = kubeconfig_path

        if not namespace:
            if deck:
                self._namespace = deck["environment"][0]["namespace"] or "default"
            else:
                self._namespace = "default"
        else:
            self._namespace = namespace

        self._api_client = config.new_client_from_config(kubeconfig_path)
        self._core_api = client.CoreV1Api(self._api_client)
        self._networking_api = client.NetworkingV1beta1Api(self._api_client)

    @property
    def is_available(self):
        try:
            self._core_api.get_api_resources()
            return True
        except ApiException:
            return False

    def delete_pod(self, pod_name):
        delete_options = client.V1DeleteOptions()
        try:
            return self._core_api.delete_namespaced_pod(name=pod_name, namespace=self._namespace, body=delete_options)
        except MaxRetryError:
            raise UnikubeClusterUnavailableError

    def get_pods(self):
        try:
            return self._core_api.list_namespaced_pod(self._namespace, watch=False)
        except MaxRetryError:
            raise UnikubeClusterUnavailableError

    def get_pod(self, pod_name: str):
        pods = self.get_pods()
        for pod in pods.items:
            if pod.metadata.name == pod_name:
                return pod
        return None

    def get_logs(self, pod, follow, container=None):
        if follow:
            w = watch.Watch()
            try:
                for log in w.stream(
                    self._core_api.read_namespaced_pod_log, name=pod, namespace=self._namespace, container=container
                ):
                    click.echo(log)
            except ApiException as e:
                console.error(str(e))
        else:
            try:
                ret = self._core_api.read_namespaced_pod_log(name=pod, namespace=self._namespace, container=container)
            except ApiException as e:
                console.error(str(e))
            else:
                return ret

    def get_ingress(self):
        ret = self._networking_api.list_namespaced_ingress(self._namespace, watch=False)
        return ret

    def get_configmap(self, name=None):
        ret = self._core_api.list_namespaced_config_map(self._namespace, watch=False)
        if name:
            ret = next(filter(lambda x: x.metadata.name == name, ret.items))
        return ret

    def get_serviceaccount_tokens(self, app_name):
        cmd = [
            f"cat {settings.SERVICE_TOKEN_FILENAME}",
            f"cat {settings.SERVICE_CERT_FILENAME}",
        ]

        pods = self.get_pods()
        target = None
        for pod in pods.items:
            # match the first pod from this app
            if pod.metadata.name.startswith(app_name):
                target = pod
                break
        if target is None:
            print(app_name)
            return None
        # select the first container
        container_name = target.spec.containers[0].name
        response = stream(
            self._core_api.connect_get_namespaced_pod_exec,
            target.metadata.name,
            self._namespace,
            container=container_name,
            command="/bin/sh",
            stderr=True,
            stdin=True,
            stdout=True,
            tty=False,
            _preload_content=False,
        )
        std_out = []
        std_err = []
        while response.is_open():
            response.update(timeout=1)
            if response.peek_stdout():
                std_out.append(response.read_stdout())
            if response.peek_stderr():
                std_err.append(response.read_stderr())
            if cmd:
                c = cmd.pop(0)
                response.write_stdin(c + "\n")
            else:
                break
        if std_out:
            return std_out

    def get_pods_for_workload(self, name: str, namespace: str) -> List[str]:
        result = []
        name = name.split("-")
        pods = self._core_api.list_namespaced_pod(namespace)
        for pod in pods.items:
            pod_name = pod.metadata.name.split("-")
            if all(x == y for x, y in zip(name, pod_name)) and len(pod_name) - 2 == len(name):
                # this pod name containers all segments of name
                result.append(pod.metadata.name)
        return result
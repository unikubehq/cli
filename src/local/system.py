# -*- coding: utf-8 -*-
import os
import subprocess
from typing import Tuple

import click
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
from urllib3.exceptions import MaxRetryError

import src.cli.console as console
from src.local.exceptions import UnikubeClusterUnavailableError


class CMDWrapper(object):
    base_command = None

    class CMDException(Exception):
        pass

    def __init__(self, debug_output=False):
        self._debug_output = debug_output

    def _execute(self, arguments, stdin: str = None) -> subprocess.Popen:
        cmd = [self.base_command] + arguments
        kwargs = self._get_kwargs()
        process = subprocess.Popen(cmd, **kwargs)
        if stdin:
            process.communicate(stdin)
        try:
            process.wait()
        except KeyboardInterrupt:
            try:
                process.terminate()
            except OSError:
                pass
            process.wait()
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

    def __init__(self, provider_data, debug_output=False):
        if not provider_data.kubeconfig_path:
            raise ValueError("Project does not contain the kubeconfigPath parameter")
        self._provider_data = provider_data
        super(KubeCtl, self).__init__(debug_output)

    def _get_environment(self):
        env = super(KubeCtl, self)._get_environment()
        env["KUBECONFIG"] = self._provider_data.kubeconfig_path
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

    def get_ingress_data(self, namespace):
        arguments = ["get", "ingress", "--namespace", namespace]
        process = self._execute(arguments)
        output = process.stdout.read()
        # skip the header
        ingress_lines = output.split("\n")[1:]
        result = []
        for line in ingress_lines:
            line = list(filter(lambda x: x != "", line.split(" ")))
            if line:
                result.append(
                    {
                        "name": line[0],
                        "hosts": line[1],
                        "address": line[2],
                        "ports": line[3],
                    }
                )
        return result

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

    def exec_pod(self, pod, namespace, command, interactive=False):
        arguments = ["exec", "-it", pod]
        if namespace:
            arguments += ["--namespace", namespace]
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
        process = process

        if process.returncode == 0:
            return True, ""
        else:
            return (
                False,
                "Could not build the Docker image, please make sure the image can be built",
            )

    def check_running(self, name):
        arguments = ["ps"]
        process = self._execute(arguments)
        output = process.stdout.read()
        return name in output

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


class Telepresence(KubeCtl):
    base_command = "telepresence"

    def swap(
        self,
        deployment,
        image_name,
        command=None,
        namespace=None,
        envs=None,
        mounts=None,
    ):
        arguments = ["--swap-deployment", deployment]
        if namespace:
            arguments = arguments + ["--namespace", namespace]
        arguments = arguments + ["--docker-run", "--rm"]
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

        process = self._execute(arguments)
        if process.returncode != 0:
            console.error("There was an error with switching the deployment, please find details above")

    def _get_environment(self):
        env = super(Telepresence, self)._get_environment()
        env["TELEPRESENCE_USE_DEPLOYMENT"] = "1"
        return env


class KubeAPI(object):
    def __init__(self, provider_data, deck):
        self._provider_data = provider_data
        self._deck = deck
        self._namespace = self._deck["namespace"] or "default"
        self._api_client = config.new_client_from_config(provider_data.kubeconfig_path)
        self._core_api = client.CoreV1Api(self._api_client)
        self._networking_api = client.NetworkingV1beta1Api(self._api_client)

    @property
    def is_available(self):
        try:
            self._core_api.get_api_resources()
            return True
        except ApiException:
            return False

    def get_pods(self):
        try:
            return self._core_api.list_namespaced_pod(self._namespace, watch=False)
        except MaxRetryError:
            raise UnikubeClusterUnavailableError

    def get_pod(self, pod_name):
        pods = self.get_pods()
        for pod in pods.items:
            if pod.metadata.name == pod_name:
                return pod
        return None

    def get_logs(self, pod, follow):
        if follow:
            w = watch.Watch()
            try:
                for log in w.stream(
                    self._core_api.read_namespaced_pod_log,
                    name=pod,
                    namespace=self._namespace,
                ):
                    click.echo(log)
            except ApiException as e:
                console.error(str(e))
        else:
            try:
                ret = self._core_api.read_namespaced_pod_log(name=pod, namespace=self._namespace)
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

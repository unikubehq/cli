# -*- coding: utf-8 -*-
import os
import platform
import re
import subprocess
from typing import List, Tuple, Union

import click
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream
from urllib3.exceptions import MaxRetryError

import src.cli.console as console
from src import settings
from src.local.exceptions import UnikubeClusterUnavailableError


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

    def delete_str(self, namespace, text: str):
        arguments = ["delete", "--namespace", namespace, "-f", "-"]
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


class Telepresence(KubeCtl):
    base_command = "telepresence"

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

    def intercept_count(self) -> Union[int, None]:
        arguments = ["status"]
        process = self._execute(arguments)
        status = process.stdout.readlines()

        # parse intercept count
        intercept_line = status[15]
        match = re.findall("[ ]{1,}Intercepts[ ]{1,}:(.*)[ ]{1,}total", intercept_line)
        try:
            intercept_count = int(match[0])
        except Exception:
            intercept_count = None

        return intercept_count


class KubeAPI(object):
    def __init__(self, provider_data, deck=None):
        self._provider_data = provider_data
        self._deck = deck
        if self._deck:
            self._namespace = self._deck["environment"][0]["namespace"] or "default"
        else:
            self._namespace = "default"
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

    def get_pod(self, pod_name):
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

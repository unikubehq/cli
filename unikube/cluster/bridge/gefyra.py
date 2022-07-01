from typing import List

from gefyra import api as gefyra_api
from gefyra.configuration import ClientConfiguration

from unikube.cli import console
from unikube.cluster.bridge.bridge import AbstractBridge
from unikube.cluster.system import Docker, KubeAPI
from unikube.unikubefile.unikube_file_1_0 import UnikubeFileApp


class GefyraException(Exception):
    pass


class Gefyra(AbstractBridge):
    DOCKER_IMAGE_PREFIX = "gefyra"
    DOCKER_IMAGE_NAME_PREFIX = "gefyra-switch"

    def __init__(self, kubeconfig_path: str):
        if not kubeconfig_path:
            raise ValueError("Gefyra does not contain the 'kubeconfig_path' parameter")

        self.config = ClientConfiguration(kube_config_file=kubeconfig_path)

    def intercept_count(self) -> int:
        try:
            intercept_requests = gefyra_api.list_interceptrequests(config=self.config)
        except Exception as e:
            console.debug(e)
            return 0

        return len(intercept_requests)

    def pre_cluster_up(self) -> bool:
        return True

    def post_cluster_up(self) -> bool:
        try:
            gefyra_api.up(config=self.config)
            return True
        except Exception as e:
            console.debug(e)
            return False

    def pre_cluster_down(self) -> bool:
        try:
            gefyra_api.down(config=self.config)
            return True
        except Exception as e:
            console.debug(e)
            return False

    def post_cluster_down(self) -> bool:
        return True

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
        image = self.get_docker_image(deployment=deployment)
        image_name = self.get_docker_image_name(deployment=deployment)

        # run
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

        container_name = unikube_file_app.container
        if not container_name:
            raise GefyraException("No container name provided. Please add a container to the unikube.yml")
        console.debug(f"container: {container_name}")

        try:
            k8s = KubeAPI(kubeconfig_path=kubeconfig_path, namespace=namespace)
        except Exception as e:
            console.debug(e)
            console.error("Does the cluster exist?", _exit=True)

        pods = k8s.get_pods_for_workload(name=deployment, namespace=namespace)
        for pod in pods:
            if deployment in pod:
                break
        else:
            raise GefyraException(f"Could not find a pod for deployment: {deployment}")

        console.debug("gefyra run")
        result = gefyra_api.run(
            image=image,
            name=image_name,
            command=command,
            volumes=volumes,
            namespace=namespace,
            env=env,
            env_from=f"{pod}/{container_name}",
            config=self.config,
        )
        if not result:
            console.error("Gefyra run failed.", _exit=True)

        console.debug("docker waiting for container")
        while not Docker().check_running(image_name):
            continue

        # bridge
        console.debug("gefyra bridge")
        result = gefyra_api.bridge(
            name=image_name,
            namespace=namespace,
            deployment=deployment,
            ports=unikube_file_app.ports,
            container_name=container_name,
            bridge_name=image,
            config=self.config,
        )
        if not result:
            console.error("Gefyra bridge failed.", _exit=True)

        _ = console.confirm(question="Press ENTER to stop the switch.")

        # print logs? -> gracefull exit currently not working
        # k8s = KubeAPI(kubeconfig_path=kubeconfig_path, namespace=namespace)
        # _ = k8s.get_logs(pod=pod, follow=True, container=container_name)

        console.debug("gefyra kill_switch")
        self.kill_switch(deployment=deployment)

        return True

    def is_switched(self, deployment: str, namespace: str) -> bool:
        try:
            intercept_requests = gefyra_api.list_interceptrequests(config=self.config)
        except Exception as e:
            console.debug(e)
            return 0

        if not intercept_requests:
            return False

        return True

    def kill_switch(self, deployment: str, *args, **kwargs) -> bool:
        image = self.get_docker_image(deployment=deployment)

        # unbridge
        console.debug("gefyra unbridge")
        try:
            gefyra_api.unbridge(name=image, config=self.config)
        except Exception as e:
            console.debug(e)

        # stop docker container
        console.debug("gefyra kill docker container")
        docker = Docker()
        if docker.check_running(image):
            docker.kill(name=image)

        return True


class GefyraBuilder:
    def __call__(
        self,
        kubeconfig_path: str,
        **kwargs,
    ):
        instance = Gefyra(kubeconfig_path=kubeconfig_path)
        return instance

import socket

from unikube.cli import console
from unikube.cluster.system import Docker
from unikube.unikubefile.unikube_file_1_0 import UnikubeFileApp


def _is_local_port_free(port):
    a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if a_socket.connect_ex(("127.0.0.1", int(port))) == 0:
        return False
    else:
        return True


class AbstractBridge:
    DOCKER_IMAGE_PREFIX = "bridge"
    DOCKER_IMAGE_NAME_PREFIX = "bridge-switch"

    @classmethod
    def get_docker_image(cls, deployment: str):
        tag = f"{cls.DOCKER_IMAGE_PREFIX}-{deployment}".lower()
        return tag

    @classmethod
    def get_docker_image_name(cls, deployment: str):
        tag = f"{cls.DOCKER_IMAGE_NAME_PREFIX}-{deployment}".lower()
        return tag

    def intercept_count(self) -> int:
        return 0

    def pre_cluster_up(self):
        pass

    def post_cluster_up(self):
        pass

    def pre_cluster_down(self):
        pass

    def post_cluster_down(self):
        pass

    def switch(self):
        raise NotImplementedError("Bridge switch is not implemented.")

    def is_switched(self, deployment: str, namespace: str) -> bool:
        raise NotImplementedError("Bridge is_switched is not implemented.")

    def kill_switch(self, deployment: str, namespace: str) -> bool:
        image_name = self.get_docker_image(deployment=deployment)

        docker = Docker()
        if docker.check_running(image_name):
            docker.kill(name=image_name)

        raise NotImplementedError("Bridge kill_switch is not implemented.")

    def build(self, deployment: str, namespace: str, unikube_file_app, no_build: bool):
        # grab the docker file
        context, dockerfile, target = unikube_file_app.get_docker_build()
        if not target:
            target = ""

        # check for active switch
        if self.is_switched(deployment=deployment, namespace=namespace):
            console.warning("It seems this app is already switched in another process.")

            confirmed = console.confirm(question="Do you want to kill it and switch here? [N/y]: ")
            if not confirmed:
                console.error("Switch aborted.", _exit=True)

            self.kill_switch(deployment=deployment, namespace=namespace)

        # 3.3 Build image
        image = self.get_docker_image(deployment=deployment)

        docker = Docker()
        if not docker.image_exists(image) or not no_build:
            if no_build:
                console.warning(f"Ignoring --no-build since the required image '{image}' does not exist")

            console.info(f"Building docker image for {dockerfile} with context {context}")
            status, msg = docker.build(image, context, dockerfile, target)

            if not status:
                console.debug(msg)
                console.error("Failed to build docker image.", _exit=True)

            console.success(f"Docker image successfully built: {image}")
        else:
            console.info(f"Using existing docker image: {image}")

    def _get_intercept_port(self, unikube_file_app: UnikubeFileApp, ports):
        # set the right intercept port
        port = unikube_file_app.get_port()
        if port is None:
            port = str(ports[0])
            if len(ports) > 1:
                console.warning(
                    f"No port specified although there are multiple ports available: {ports}. "
                    f"Defaulting to port {port} which might not be correct."
                )

        if port not in ports:
            console.error(f"The specified port {port} is not in the rage of available options: {ports}", _exit=True)

        if not _is_local_port_free(port):
            console.error(
                f"The local port {port} is busy. Please stop the application running on " f"this port and try again.",
                _exit=True,
            )

        return port

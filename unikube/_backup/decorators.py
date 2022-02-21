from time import sleep

import click
from utils.console import error
from utils.exceptions import UnikubeClusterUnavailableError
from utils.localsystem import K3D, KubeAPI
from utils.project import AppManager, ProjectManager


def retry_command(function):
    def wrapper(*args, **kwargs):
        try:
            res = function(*args, **kwargs)
        except UnikubeClusterUnavailableError:
            error("Cannot reach local cluster.")
            project = ProjectManager().get_active()
            app = AppManager().get_active()
            if click.confirm(f"Should we try to \"project up {project.get('name')}\"?"):
                K3D(project).up(ingress_port=None, workers=None)
                retry_count = 0
                k8s = KubeAPI(project, app)
                while not k8s.is_available and retry_count <= 30:
                    sleep(0.5)
                    retry_count += 1
                if retry_count == 30:
                    error("Could not up project.")
                    exit(1)
                res = function(*args, **kwargs)
            else:
                exit(1)
        return res

    return wrapper

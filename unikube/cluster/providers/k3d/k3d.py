import os
import re
import shutil
import subprocess
from time import sleep
from typing import Dict, List, Optional
from uuid import UUID

from semantic_version import Version

import unikube.cli.console as console
from unikube import settings
from unikube.cluster.providers.abstract_provider import AbstractProvider
from unikube.cluster.providers.k3d.storage import K3dData
from unikube.cluster.providers.types import ProviderType
from unikube.cluster.storage.cluster_data import ClusterStorage
from unikube.cluster.system import CMDWrapper, Docker


class K3d(AbstractProvider, CMDWrapper):
    provider_type = ProviderType.k3d

    base_command = "k3d"
    _cluster = []

    def __init__(self, id: UUID, name: str = None, _debug_output=False):
        # storage
        self.storage = ClusterStorage(id=id)

        # abstract kubernetes cluster
        AbstractProvider.__init__(self, id=id, name=name)

        # CMDWrapper
        self._debug_output = _debug_output

    def _clusters(self) -> List[Dict[str, str]]:
        if len(self._cluster) == 0:
            arguments = ["cluster", "list", "--no-headers"]
            process = self._execute(arguments)
            list_output = process.stdout.read()
            clusters = []
            cluster_list = [item.strip() for item in list_output.split("\n")[:-1]]
            for entry in cluster_list:
                cluster = [item.strip() for item in entry.split(" ") if item != ""]
                # todo handle this output
                if len(cluster) != 4:
                    continue
                clusters.append(
                    {
                        "name": cluster[0],
                        "servers": cluster[1],
                        "agents": cluster[2],
                        "loadbalancer": cluster[3] == "true",
                    }
                )
            self._cluster = clusters
        return self._cluster

    def get_kubeconfig(self, wait=10) -> Optional[str]:
        arguments = ["kubeconfig", "get", self.cluster_name]
        # this is a nasty busy wait, but we don't have another chance
        for i in range(1, wait):
            process = self._execute(arguments)
            if process.returncode == 0:
                break
            else:
                console.info(f"Waiting for the cluster to be ready ({i}/{wait}).")
                sleep(2)

        if process.returncode != 0:
            console.error("Something went completely wrong with the cluster spin up (or we got a timeout).", _exit=True)

        # we now need to write the kubekonfig to a file
        config = process.stdout.read().strip()
        if not os.path.isdir(os.path.join(settings.CLI_UNIKUBE_DIRECTORY, "cluster", str(self.id))):
            os.mkdir(os.path.join(settings.CLI_UNIKUBE_DIRECTORY, "cluster", str(self.id)))
        config_path = os.path.join(
            settings.CLI_UNIKUBE_DIRECTORY,
            "cluster",
            str(self.id),
            "kubeconfig.yaml",
        )
        file = open(config_path, "w+")
        file.write(config)
        file.close()
        return config_path

    def exists(self) -> bool:
        for cluster in self._clusters():
            if cluster["name"] == self.cluster_name:
                return True
        return False

    def create(
        self,
        ingress_port=None,
        workers=settings.K3D_DEFAULT_WORKERS,
    ):
        v5plus = self.version().major >= 5
        api_port = self._get_random_unused_port()

        if not ingress_port:
            publisher_port = self._get_random_unused_port()
        else:
            publisher_port = ingress_port

        arguments = [
            "cluster",
            "create",
            self.cluster_name,
            "--agents",
            str(workers),
            "--api-port",
            str(api_port),
            "--port",
            f"{publisher_port}:{settings.K3D_DEFAULT_INGRESS_PORT}@agent{':0' if v5plus else '[0]'}",
            "--servers",
            str(1),
            "--wait",
            "--timeout",
            "120s",
        ]
        self._execute(arguments)

        self.storage.name = self.cluster_name
        self.storage.provider[self.provider_type.name] = K3dData(
            api_port=api_port,
            publisher_port=publisher_port,
            kubeconfig_path=self.get_kubeconfig(),
        )
        self.storage.save()

        return True

    def start(self):
        arguments = ["cluster", "start", self.cluster_name]
        p = self._execute(arguments)
        if p.returncode != 0:
            return False

        _ = self.get_kubeconfig()
        return True

    def stop(self):
        arguments = ["cluster", "stop", self.cluster_name]
        self._execute(arguments)
        return True

    def delete(self):
        arguments = ["cluster", "delete", self.cluster_name]
        self._execute(arguments)

        try:
            self.storage.delete()
        except Exception as e:
            console.debug(e)

        try:
            folder_path = os.path.join(settings.CLI_UNIKUBE_DIRECTORY, "cluster", str(self.id))
            shutil.rmtree(folder_path)
        except Exception as e:
            console.debug(e)

        return True

    def version(self) -> Version:
        process = subprocess.run([self.base_command, "--version"], capture_output=True, text=True)
        output = str(process.stdout).strip()
        version_str = re.search(r"(\d+\.\d+\.\d+)", output).group(1)
        return Version(version_str)

    def ready(self) -> bool:
        return Docker().check_running(self.cluster_name)


class K3dBuilder:
    def __init__(self):
        self._instances = {}

    def __call__(
        self,
        id: UUID,
        name: str = None,
        **_ignored,
    ):
        # get instance from cache
        instance = self._instances.get(id, None)
        if instance:
            return instance

        # create instance
        instance = K3d(id, name=name)
        self._instances[id] = instance

        return instance

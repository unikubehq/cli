# -*- coding: utf-8 -*-
import os
from typing import List, Optional, Tuple

from src.context.types import ContextData
from src.unikubefile.unikube_file import UnikubeFile, UnikubeFileError


class UnikubeFile_1_0(UnikubeFile):
    def __init__(self, path: str, data: dict):
        super().__init__(path=path, data=data)
        self.path = path

        self._data = data
        self._verify()

        # set the first app active for all query methods
        self._app = self.get_apps()[0]
        self._path = os.path.dirname(path)

    def get_context(self):
        context = self._data.get("context", None)
        if not context:
            return ContextData()

        return ContextData(
            organization=context.get("organization", None),
            project=context.get("project", None),
            deck=context.get("deck", None),
        )

    def _verify(self):
        self._check_required("apps", self._data, "root")

    def _check_required(self, _keys, node, node_title):
        if type(_keys) == list:
            for _key in _keys:
                if _key not in node:
                    raise UnikubeFileError(f"Unikubefile not valid, missing key {_key} not in {node_title}")
        else:
            if _keys not in node:
                raise UnikubeFileError(f"Unikubefile not valid, missing key {_keys} not in {node_title}")

    # def set_app(self, app):
    #     if app not in self.get_apps():
    #         raise UnikubeFileError(f"the app '{app}' is not part of this Unikubefile")

    def get_apps(self):
        apps = list(self._data["apps"].keys())
        return apps

    def get_docker_build(self) -> Tuple[str, str, str]:
        app = self._data["apps"][self._app]
        build = app.get("build")
        if build:
            base_path = os.path.dirname(self.path)
            path = os.path.abspath(os.path.join(base_path, build["context"]))
            dockerfile = os.path.join(base_path, build.get("dockerfile", "Dockerfile"))
            return path, dockerfile, build.get("target", "")
        else:
            return os.path.abspath("."), "Dockerfile", ""

    def get_command(self, **format) -> Optional[str]:
        app = self._data["apps"][self._app]
        command = app.get("command")
        if command:
            command = command.format(**format)
            return command.split(" ")
        else:
            return None

    def get_deployment(self) -> Optional[str]:
        app = self._data["apps"][self._app]
        deployment = app.get("deployment")
        if deployment:
            return str(deployment)
        else:
            return None

    def get_mounts(self) -> List[Tuple[str, str]]:
        app = self._data["apps"][self._app]
        volumes = app.get("volumes")
        mounts = []
        if volumes:
            base_path = os.path.dirname(self.path)
            for mount in volumes:
                mount = mount.split(":")
                source = os.path.abspath(os.path.join(base_path, mount[0]))
                target = mount[1]
                mounts.append((source, target))
        return mounts

    def get_environment(self) -> List[Tuple[str, str]]:
        app = self._data["apps"][self._app]
        variables = app.get("environment")
        if variables is None:
            # fallback to the env keyword
            variables = app.get("env")
        envs = []
        if variables:
            for env in variables:
                envs.append(list(env.items())[0])
        return envs

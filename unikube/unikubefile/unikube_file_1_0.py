# -*- coding: utf-8 -*-
import os
from typing import List, Optional, Tuple

from pydantic import BaseModel

from unikube.context.types import ContextData
from unikube.unikubefile.unikube_file import UnikubeFile


class UnikubeFileContext(BaseModel):
    organization: Optional[str] = None
    project: Optional[str] = None
    deck: Optional[str] = None


class UnikubeFileBuild(BaseModel):
    context: str
    dockerfile: Optional[str] = "Dockerfile"
    target: Optional[str] = None


class UnikubeFileApp(BaseModel):
    unikube_file: str
    name: str
    build: UnikubeFileBuild
    deployment: str
    port: Optional[int] = None
    command: str
    volumes: Optional[List[str]] = None
    env: Optional[List[dict]] = None

    def get_docker_build(self) -> Tuple[str, str, str]:
        if self.build:
            base_path = os.path.dirname(self.unikube_file)
            path = os.path.abspath(os.path.join(base_path, self.build.context))
            dockerfile = os.path.join(base_path, self.build.dockerfile)
            target = self.build.target
            return path, dockerfile, target
        else:
            return os.path.abspath("."), "Dockerfile", ""

    def get_command(self, **format) -> Optional[str]:
        if not self.command:
            return None

        command = self.command.format(**format)
        return command.split(" ")

    def get_port(self) -> Optional[str]:
        if self.port:
            return str(self.port)
        else:
            return None

    def get_deployment(self) -> Optional[str]:
        if self.deployment:
            return str(self.deployment)
        else:
            return None

    def get_mounts(self) -> List[Tuple[str, str]]:
        mounts = []
        if self.volumes:
            base_path = os.path.dirname(self.unikube_file)
            for mount in self.volumes:
                mount = mount.split(":")
                source = os.path.abspath(os.path.join(base_path, mount[0]))
                target = mount[1]
                mounts.append((source, target))
        return mounts

    def get_environment(self) -> List[Tuple[str, str]]:
        envs = []
        if self.env:
            for env in self.env:
                envs.append(list(env.items())[0])
        return envs


class UnikubeFile_1_0(UnikubeFile, BaseModel):
    version: Optional[str]
    context: Optional[UnikubeFileContext] = None
    apps: List[UnikubeFileApp]

    def get_context(self) -> ContextData:
        if not self.context:
            return ContextData()

        return ContextData(
            organization_id=self.context.organization,
            project_id=self.context.project,
            deck_id=self.context.deck,
        )

    def get_app(self, name: str = None) -> UnikubeFileApp:
        # default name
        if not name:
            name = "default"

        for app in self.apps:
            if app.name == name:
                return app

        if name != "default":
            raise ValueError("Invalid name.")

        return self.apps[0]

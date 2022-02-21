import os
from typing import Union

import click
import yaml

from unikube.settings import UNIKUBE_FILE
from unikube.unikubefile.unikube_file import (
    UnikubeFile,
    UnikubeFileError,
    UnikubeFileNotFoundError,
    UnikubeFileVersionError,
)
from unikube.unikubefile.unikube_file_1_0 import UnikubeFile_1_0


class UnikubeFileSelector:
    def __init__(self, options: dict):
        self.options = options

    @staticmethod
    def __convert_apps_to_list(path_unikube_file: str, data: dict):
        apps_list = []
        for name, item in data["apps"].items():
            item["unikube_file"] = path_unikube_file
            item["name"] = name
            apps_list.append(item)
        data["apps"] = apps_list
        return data

    def get(self, path_unikube_file: str = None) -> Union[UnikubeFile, UnikubeFile_1_0, None]:
        # default file path
        if not path_unikube_file:
            path_unikube_file = os.path.join(os.getcwd(), UNIKUBE_FILE)

        # load unikube file + get version
        try:
            with click.open_file(path_unikube_file) as unikube_file:
                data = yaml.load(unikube_file, Loader=yaml.FullLoader)
        except FileNotFoundError:
            raise UnikubeFileNotFoundError

        # add & format data
        try:
            data = self.__convert_apps_to_list(path_unikube_file=path_unikube_file, data=data)
        except Exception:
            raise UnikubeFileError("Invalid unikube file.")

        # version
        version = str(data.get("version", "latest"))
        data["version"] = version

        # get class
        unikube_file_class = self.options.get(version)
        if not unikube_file_class:
            raise UnikubeFileVersionError

        return unikube_file_class(**data)


unikube_file_selector = UnikubeFileSelector(
    options={
        "latest": UnikubeFile_1_0,
        "1": UnikubeFile_1_0,
        "1.0": UnikubeFile_1_0,
    }
)

from typing import Union

import click
import yaml

from src.unikubefile.unikube_file import UnikubeFile, UnikubeFileNotFoundError, UnikubeFileVersionError
from src.unikubefile.unikube_file_1_0 import UnikubeFile_1_0


class UnikubeFileSelector:
    def __init__(self, options: dict):
        self.options = options

    def get(self, path_unikube_file: str) -> Union[UnikubeFile, UnikubeFile_1_0, None]:
        # load unikube file + get version
        try:
            with click.open_file(path_unikube_file) as unikube_file:
                data = yaml.load(unikube_file, Loader=yaml.FullLoader)
        except FileNotFoundError:
            raise UnikubeFileNotFoundError

        version = data.get("version", "latest")

        # get class
        unikube_file_class = self.options.get(version)
        if not unikube_file_class:
            raise UnikubeFileVersionError

        return unikube_file_class(
            path=path_unikube_file,
            data=data,
        )


unikube_file_selector = UnikubeFileSelector(
    options={
        "latest": UnikubeFile_1_0,
        "1": UnikubeFile_1_0,
        "1.0": UnikubeFile_1_0,
    }
)

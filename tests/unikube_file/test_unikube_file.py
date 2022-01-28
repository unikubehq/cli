import os
import unittest

from src.unikubefile.selector import unikube_file_selector
from src.unikubefile.unikube_file import UnikubeFileError


class SelectorTest(unittest.TestCase):
    def test_version_latest(self):
        path_unikube_file = "tests/unikube_file/unikube_version_latest.yaml"
        unikube_file = unikube_file_selector.get(path_unikube_file)
        self.assertEqual("latest", unikube_file.version)

    def test_version_1(self):
        path_unikube_file = "tests/unikube_file/unikube_version_1.yaml"
        unikube_file = unikube_file_selector.get(path_unikube_file)
        self.assertEqual("1", unikube_file.version)

    def test_apps_invalid(self):
        path_unikube_file = "tests/unikube_file/unikube_apps_invalid.yaml"
        with self.assertRaises(UnikubeFileError):
            _ = unikube_file_selector.get(path_unikube_file)


class UnikubeFileTest(unittest.TestCase):
    def test_get_app_none(self):
        path_unikube_file = "tests/unikube_file/unikube.yaml"
        unikube_file = unikube_file_selector.get(path_unikube_file)

        unikube_file_app = unikube_file.get_app()
        self.assertEqual("your-app-01", unikube_file_app.name)

    def test_get_app_name(self):
        path_unikube_file = "tests/unikube_file/unikube.yaml"
        unikube_file = unikube_file_selector.get(path_unikube_file)

        unikube_file_app = unikube_file.get_app(name="your-app-01")
        self.assertEqual("your-app-01", unikube_file_app.name)

    def test_get_app_default(self):
        path_unikube_file = "tests/unikube_file/unikube_apps_default.yaml"
        unikube_file = unikube_file_selector.get(path_unikube_file)

        unikube_file_app = unikube_file.get_app()
        self.assertEqual("default", unikube_file_app.name)


class UnikubeFileAppTest(unittest.TestCase):
    def setUp(self) -> None:
        path_unikube_file = "tests/unikube_file/unikube.yaml"
        unikube_file = unikube_file_selector.get(path_unikube_file)
        self.unikube_file_app = unikube_file.get_app()

    def test_get_docker_build(self):
        context, dockerfile, target = self.unikube_file_app.get_docker_build()
        self.assertEqual(os.path.abspath(os.path.join(os.getcwd(), "tests/unikube_file/.")), context)
        self.assertEqual("tests/unikube_file/Dockerfile", dockerfile)
        self.assertEqual("target", target)

    def test_get_command(self):
        command = self.unikube_file_app.get_command()
        self.assertEqual("bash".split(" "), command)

    def test_get_port(self):
        port = self.unikube_file_app.get_port()
        self.assertEqual(str(8000), port)

    def test_get_deployment(self):
        deployment = self.unikube_file_app.get_deployment()
        self.assertEqual("deployment", deployment)

    def test_get_mounts(self):
        volumes = self.unikube_file_app.get_mounts()
        self.assertEqual([(os.path.abspath(os.path.join(os.getcwd(), "tests/unikube_file/src")), "/app")], volumes)

    def test_get_environment(self):
        env = self.unikube_file_app.get_environment()
        self.assertEqual([("VARIABLE-01", "variable-01")], env)

from unittest.mock import patch

from tests.login_testcase import LoginTestCase
from unikube.cli import init
from unikube.context import ClickContext


class InitTestCase(LoginTestCase):
    @patch("unikube.cli.init.get_env")
    @patch("unikube.cli.init.get_volume")
    @patch("unikube.cli.init.confirm")
    @patch("unikube.cli.init.get_command")
    @patch("unikube.cli.init.get_port")
    @patch("unikube.cli.init.get_deployment")
    @patch("unikube.cli.init.get_target")
    @patch("unikube.cli.init.get_context")
    @patch("unikube.cli.init.get_docker_file")
    @patch("unikube.cli.init.deck_list")
    @patch("unikube.cli.init.project_list")
    @patch("unikube.cli.init.organization_list")
    def test_init(
        self,
        organization_list,
        project_list,
        deck_list,
        get_docker_file,
        get_context,
        get_target,
        get_deployment,
        get_port,
        get_command,
        confirm,
        get_volume,
        get_env,
    ):
        organization_list.return_value = "ceba2255-3113-4a2c-af7a-7e0c9e73cd0c"
        project_list.return_value = "b464a6a7-7367-41d3-92a3-d3d98ed10cb5"
        deck_list.return_value = "4634368f-1751-40ae-9cd7-738fcb656a0d"
        get_docker_file.return_value = "Dockerfile"
        get_context.return_value = "."
        get_target.return_value = ""
        get_deployment.return_value = "project-service"
        get_port.return_value = "9000"
        get_command.return_value = ""
        get_volume.return_value = ""
        get_env.return_value = ""
        confirm.return_value = "y"

        result = self.runner.invoke(
            init.init,
            ["--stdout"],
            obj=ClickContext(),
        )

        assert organization_list.called
        assert project_list.called
        assert deck_list.called
        assert get_docker_file.called
        assert get_context.called
        assert get_target.called
        assert get_deployment.called
        assert get_port.called
        assert get_command.called
        assert get_volume.called
        assert get_env.called

        self.assertIn(organization_list.return_value, result.output)
        self.assertIn(project_list.return_value, result.output)
        self.assertIn(deck_list.return_value, result.output)
        self.assertIn(get_docker_file.return_value, result.output)
        self.assertIn(get_deployment.return_value, result.output)
        self.assertIn(get_port.return_value, result.output)

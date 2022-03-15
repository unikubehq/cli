from typing import List, Optional, Tuple

import click
import yaml
from pydantic import BaseModel

from unikube.cli import console
from unikube.cli.console import confirm, deck_list, organization_list, project_list


class UnikubeFileBuild(BaseModel):
    context: str = "."
    dockerfile: str = "Dockerfile"
    target: str = ""


class UnikubeFileContext(BaseModel):
    organization: str
    project: str
    deck: str


class UnikubeFileApp(BaseModel):
    context: UnikubeFileContext
    build: UnikubeFileBuild
    deployment: str
    port: int
    command: Optional[str]
    volumes: Optional[List[str]]
    env: Optional[List[str]]


class UnikubeDumper(yaml.SafeDumper):
    """Custom dumper for nice list identation.

    See https://stackoverflow.com/questions/25108581/python-yaml-dump-bad-indentation
    """

    def increase_indent(self, flow=False, indentless=False):
        return super(UnikubeDumper, self).increase_indent(flow, False)


def _generate_unikube_file(apps: List[UnikubeFileApp], to_file: bool = True):
    result = {"version": "1", "apps": {}}
    for app in apps:
        result["apps"].update({"app": app.dict(exclude_unset=True)})

    if to_file:
        with open("unikube.yaml", "w") as unikube_file:
            yaml.dump(result, unikube_file, Dumper=UnikubeDumper, sort_keys=False)
    else:
        console.echo(yaml.dump(result, Dumper=UnikubeDumper, sort_keys=False))

    return True


def prompt_headline(text: str):
    return click.echo(click.style(text + "\n", bold=True, underline=True))


def format_question(question, question_only=False):
    if not question_only:
        mark = click.style("? ", fg=(69, 208, 147), bold=True)
    else:
        mark = ""
    question_ = click.style(question, bold=True)
    return f"{mark}{question_}"


def prompt_for_choice(question: str, list_func, ctx):
    click.echo(format_question(question, question_only=True))
    result = list_func(ctx)
    return result


def path_validator(input_string: str):
    return len(input_string) == 0 or (isinstance(input_string, str) and ":" in input_string)


def env_validator(input_string: str):
    return len(input_string) == 0 or (isinstance(input_string, str) and "=" in input_string)


def get_docker_file():
    return console.input("Dockerfile (default: 'Dockerfile')", "Dockerfile")


def get_context():
    console.echo("What's the context for building your docker image?")
    console.echo("For more information on 'docker build context' please see:")
    console.link("https://docs.docker.com/engine/reference/commandline/build/#extended-description")
    return console.input("Build Context (default: '.')", ".")


def get_target():
    console.echo("What's the target stage for building your docker image?")
    console.echo("For more information on Docker's target stage please see:")
    console.link("https://docs.docker.com/engine/reference/commandline/build/#specifying-target-build-stage---target")
    return console.input("Target (optional)", "")


def get_deployment():
    return console.input("What's the name of the deployment?", mandatory=True)


def get_port():
    return console.input(
        "What's the port of it's container?",
        mandatory=True,
        validate=lambda x: x.isnumeric,
        invalid_message="Input must be a number.",
    )


def get_command():
    return console.input("What command should be executed on start? (optional)", "")


def get_env():
    console.input(
        "Enter env variables (e.g. DEBUG=true)", "", validate=env_validator, invalid_message="Input must contain '='."
    )


def get_volume():
    return console.input(
        "Enter a volume mapping (e.g. </local_path>:</container_path>)",
        "",
        validate=path_validator,
        invalid_message="Input must contain ':'.",
    )


def collect_app_data(ctx) -> UnikubeFileApp:
    click.echo("")
    click.echo("This command helps to generate a unikube.yaml file.")
    click.echo("For detailed information concerning the file please visit:")
    console.link("https://unikube.io/docs/guides/developing-with-unikube.html#unikubefile")
    click.echo("")
    prompt_headline("Unikube Information")

    # TODO this could probably be pulled from the current cli context
    organization = prompt_for_choice("Which organization does the project belong to?", organization_list, ctx)
    project = prompt_for_choice("Which project does the service run in?", project_list, ctx)
    deck = prompt_for_choice("Which deck contains the deployment?", deck_list, ctx)

    unikube_context = UnikubeFileContext(organization=organization, deck=deck, project=project)

    # Collect docker information
    click.echo("")
    prompt_headline("Docker information")
    dockerfile = get_docker_file()
    context = get_context()
    target = get_target()

    build = UnikubeFileBuild(
        dockerfile=dockerfile,
        context=context,
        target=target,
    )

    deployment = get_deployment()
    port = get_port()
    command = get_command()

    volumes = []
    volumes_needed = confirm("Add volume mappings [N/y]")
    if volumes_needed:
        click.echo("To stop, just hit ENTER.")
        volume = get_volume()
        volumes.append(volume)
        while volume:
            volume = get_volume()

    env_needed = confirm("Add env variables [N/y]")
    envs = []
    if env_needed:
        click.echo("To stop, just hit ENTER.")
        env = get_env()
        envs.append(env)
        while env:
            env = get_env()
            envs.append(env)

    unikube_app_kwargs = {
        "build": build,
        "context": unikube_context,
        "deployment": deployment,
        "port": port,
    }

    if command:
        unikube_app_kwargs.update(
            {
                "command": command,
            }
        )

    if volumes:
        unikube_app_kwargs.update(
            {
                "volumes": volumes,
            }
        )

    if envs:
        unikube_app_kwargs.update({"env": envs})

    app = UnikubeFileApp(**unikube_app_kwargs)

    return app


# TODO add options to command to shorten prompts / make command scriptable
@click.command()
@click.option("--stdout", "-s", help="Print file output to console.", is_flag=True)
@click.pass_obj
def init(ctx, stdout):
    _ = ctx.auth.refresh()

    # We plan to support multiple apps in the future.
    results = [collect_app_data(ctx)]

    result = _generate_unikube_file(results, to_file=not stdout)
    if result:
        console.echo("")
        success = click.style("Successfully generated unikube.yaml!", bold=True, underline=True)
        console.echo(f"🚀  {success}\n")

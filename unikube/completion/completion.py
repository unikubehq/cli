import textwrap
from typing import List

import click

from unikube.cli import console

from .templates import TEMPLATES


def align_spacing(string: str, spaces: int) -> str:
    """
    Prefix multiline string with given number of spaces.

    Just a helper to make the scripts more readable.
    """
    return textwrap.indent(textwrap.dedent(string), " " * spaces)


def get_subcommands(command: dict) -> dict:
    """Extract subcommands from Click's information dictionary retrieved via `to_info_dict`."""
    if "commands" in command:
        commands = command["commands"]
        return {key: get_options(command["commands"][key]) for key in commands.keys()}
    return {}


def get_options(command: dict) -> List[str]:
    """Extract options from Click's information dictionary retrieved via `to_info_dict`."""
    params = command["params"]
    result = []
    for param in params:
        result.extend(filter(lambda x: "--" in x, param["opts"]))
    return result


def render_subcommand_completion(current_command: str, commands: List):
    """Renders case statement for subcommand completion."""
    return """
    ({current_command})
        coms="{commands}"
        COMPREPLY=($(compgen -W "${{coms}}" -- ${{cur}}))
        __ltrim_colon_completions "$cur"
        return 0;
        ;;
    """.format(
        current_command=current_command, commands=" ".join(commands)
    )


def render_options_case(command: str, func_name: str):
    """Renders case statement (function call) for options completion."""
    return align_spacing(
        """
        ({command})
            {func_name}
            ;;""".format(
            command=command, func_name=func_name
        ),
        12,
    )


def render_command_options(command: str, options: List[str]) -> str:
    """Generate bash option string for a command."""
    return """
        ({command})
            opts="${{opts}} {options}"
            ;;""".format(
        command=command, options=" ".join(options)
    )


def render_flag_completion_func(command_dict: dict, name: str) -> (str, str):
    """Renders function for flag completion of command and its subcommands."""
    subcommands = get_subcommands(command_dict)
    options = get_options(command_dict)

    func_name = "__unikube_complete_flags_{name}".format(name=name)

    if subcommands:
        subcommand_cases = align_spacing(
            "\n".join([render_command_options(c[0], c[1]) for c in subcommands.items()]), 16
        )

        return func_name, align_spacing(
            """
        {func_name}() {{
            if [[ $com == $prev ]]; then
                opts="${{opts}} {options}"
            else
                case "$prev" in
                    {subcommand_cases}
                esac
            fi
        }}
        """.format(
                func_name=func_name, options=" ".join(options), subcommand_cases=subcommand_cases
            ),
            0,
        )
    return func_name, align_spacing(
        """
    {func_name}() {{
        opts="${{opts}} {options}"
    }}
    """.format(
            func_name=func_name,
            options=" ".join(options),
        ),
        0,
    )


def render_bash(cli):
    """Renders bash completion script and prints it."""
    with click.Context(cli) as ctx:
        info = ctx.to_info_dict()

        template = TEMPLATES["bash"]

        # static information for rendering
        # could be dynamic in the future (e.g. for aliases)
        function = "_unikube_complete"
        aliases = ["unikube"]
        compdefs = "\n".join(["complete -o default -F {} {}".format(function, alias) for alias in aliases])

        # Based on click's info dict retrieve information about commands and flags.
        # These are then used to render certain parts of the completion.
        commands = info["command"]["commands"].keys()
        command_list = []
        subcommands = []
        functions = []
        for command in commands:
            subs = get_subcommands(info["command"]["commands"][command])
            name, func = render_flag_completion_func(info["command"]["commands"][command], command)
            desc = []
            if name and func:
                functions.append(func)
                desc = [render_options_case(command, name)]

            if len(subs.keys()):
                subcommands.append(render_subcommand_completion(command, list(subs.keys())))

            if len(desc):
                command_list.append("\n".join(desc))

        # Render template with all retrieved information.
        output = template.format(
            function=function,
            flag_complete_functions="\n".join(functions),
            opts=" ".join(sorted([])),
            coms=" ".join(commands),
            command_list="\n".join(command_list),
            compdefs=compdefs,
            subcommands="\n".join(subcommands),
        )

        console.echo(output)


def render_completion_script(cli, shell: str):
    """Renders a completion for a given shell."""
    SUPPORTED_SHELLS = ["bash"]

    if shell not in SUPPORTED_SHELLS:
        console.error(
            "{} is not supported. Following shells are supported: {}.".format(shell, ", ".join(SUPPORTED_SHELLS)),
            _exit=True,
        )

    if shell == "bash":
        render_bash(cli)

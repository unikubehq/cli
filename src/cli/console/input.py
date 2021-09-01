import inquirer

import src.cli.console as console


def resolve_duplicates(choices: list, identifiers: list):
    # detect duplicates
    duplicates_mask = [True if choices.count(choice) > 1 else False for choice in choices]

    # add identifiers to duplicates
    choices_resolved = []
    for choice, identifier, duplicate in zip(choices, identifiers, duplicates_mask):
        if duplicate:
            choices_resolved.append(f"{choice} ({identifier})")
        else:
            choices_resolved.append(choice)

    return choices_resolved


# input
def list(
    message: str,
    choices: list,
    identifiers: list = None,
    allow_duplicates: bool = False,
    message_no_choices: str = "No choices available!",
):
    # choices exist
    if not len(choices) > 0:
        console.info(message_no_choices)
        return None

    # handle duplicates
    if not allow_duplicates:
        if identifiers:
            choices_display = resolve_duplicates(choices=choices, identifiers=identifiers)
        else:
            choices_display = set(choices)

    else:
        choices_display = choices

    # prompt
    questions = [
        inquirer.List(
            "select",
            message=message,
            choices=choices_display,
        ),
    ]
    answers = inquirer.prompt(questions)
    if not answers:
        return None

    return answers.get("select", None)

from typing import List

from InquirerPy import inquirer

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


def exclude_by_identifier(choices_display: List[str], identifiers: List[str], excludes: List[str]) -> List[str]:
    if not excludes:
        return choices_display

    choices_excluded = []
    for choice, identifier in zip(choices_display, identifiers):
        if any(exclude in choice for exclude in excludes) or identifier in excludes:
            continue
        choices_excluded.append(choice)
    return choices_excluded


# input
def list(
    message: str,
    choices: list,
    identifiers: list = None,
    excludes: list = None,
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

    # exclude
    choices_excluded = exclude_by_identifier(
        choices_display=choices_display, identifiers=identifiers, excludes=excludes
    )

    # prompt
    answer = inquirer.fuzzy(
        message=message,
        choices=choices_excluded,
    ).execute()
    if not answer:
        return None

    return answer

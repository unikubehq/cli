import re
from typing import Any, Callable, List, Tuple, Union

from InquirerPy import inquirer
from InquirerPy.utils import InquirerPyValidate

import unikube.cli.console as console
from unikube.cli.console.prompt import UpdatableFuzzyPrompt
from unikube.settings import INQUIRER_STYLE


def get_identifier_or_pass(selection: str) -> str:
    # get identifier if available
    # example: "PROJECT_NAME (IDENTIFIER)"

    identifier_search = re.search("(?<=\\()[^)]*(?=\\))", selection)
    try:
        project_argument = identifier_search.group(0)
    except Exception:
        project_argument = selection

    return project_argument


def resolve_duplicates(
    choices: List[str],
    identifiers: List[str],
    help_texts: Union[List[str], None] = None,
    help_texts_always: bool = False,
) -> List[str]:
    # detect duplicates
    duplicates_mask = [True if choices.count(choice) > 1 else False for choice in choices]

    # add identifiers to duplicates
    choices_resolved = []
    for choice, identifier, duplicate in zip(choices, identifiers, duplicates_mask):
        if duplicate:
            choices_resolved.append(f"{choice} ({identifier})")
        else:
            choices_resolved.append(choice)

    # help texts
    def add_help_text(choice, help_text):
        return f"{choice} - {help_text}"

    choices_resolved_with_help_text = []
    if help_texts:
        for choice, help_text, duplicate in zip(choices_resolved, help_texts, duplicates_mask):
            # add help_text always
            if help_texts_always and help_text:
                choices_resolved_with_help_text.append(add_help_text(choice, help_text))
                continue

            # add help_text for duplicates only
            if duplicate and help_text:
                choices_resolved_with_help_text.append(add_help_text(choice, help_text))
            else:
                choices_resolved_with_help_text.append(choice)

        choices_resolved = choices_resolved_with_help_text

    return choices_resolved


def filter_by_identifiers(choices: List[str], identifiers: List[str], _filter: Union[List[str], None]) -> List[str]:
    if _filter is None:
        return choices

    choices_filtered = []
    for choice, identifier in zip(choices, identifiers):
        if any(f in choice for f in _filter) or identifier in _filter:
            choices_filtered.append(choice)
    return choices_filtered


def exclude_by_identifiers(choices: List[str], identifiers: List[str], excludes: Union[List[str], None]) -> List[str]:
    if not excludes:
        return choices

    choices_excluded = []
    for choice, identifier in zip(choices, identifiers):
        if any(exclude in choice for exclude in excludes) or identifier in excludes:
            continue
        choices_excluded.append(choice)
    return choices_excluded


def prepare_choices(identifiers, choices, help_texts, _filter, allow_duplicates, excludes):
    # handle duplicates
    if not allow_duplicates:
        if identifiers:
            choices_duplicates = resolve_duplicates(choices=choices, identifiers=identifiers, help_texts=help_texts)
        else:
            choices_duplicates = set(choices)
    else:
        choices_duplicates = choices

    # filter
    choices_filtered = filter_by_identifiers(choices=choices_duplicates, identifiers=identifiers, _filter=_filter)
    # exclude
    return exclude_by_identifiers(choices=choices_filtered, identifiers=identifiers, excludes=excludes)


# input
def list(
    message: str,
    choices: List[str],
    identifiers: Union[List[str], None] = None,
    filter: Union[List[str], None] = None,
    excludes: Union[List[str], None] = None,
    help_texts: Union[List[str], None] = None,
    allow_duplicates: bool = False,
    message_no_choices: str = "No choices available!",
    multiselect: bool = False,
    transformer: Callable[[Any], str] = None,
    update_func: Callable[[], Tuple[List[str], List[str], List[str]]] = None,
) -> Union[None, List[str]]:
    choices_excluded = prepare_choices(identifiers, choices, help_texts, filter, allow_duplicates, excludes)

    # choices exist
    if not len(choices_excluded) > 0:
        console.info(message_no_choices)
        return None

    kwargs = {
        "message": message,
        "choices": choices_excluded,
        "multiselect": multiselect,
        "transformer": transformer,
        "keybindings": {"toggle": [{"key": "space"}]},
    }

    if update_func:
        update_wrapper = lambda: prepare_choices(*update_func(), filter, allow_duplicates, excludes)  # noqa: E731
        kwargs.update({"update_func": update_wrapper})

    # prompt
    answer = UpdatableFuzzyPrompt(**kwargs).execute()
    if not answer:
        return None

    return answer


def input(
    text: str,
    default: str = "",
    mandatory: bool = False,
    validate: InquirerPyValidate = None,
    invalid_message: str = "",
):
    kwargs = {}
    if mandatory:
        kwargs.update(
            {
                "validate": lambda result: len(result) > 0,
                "invalid_message": "Input cannot be empty.",
            }
        )
    if validate and invalid_message:
        kwargs.update({"validate": validate, "invalid_message": invalid_message})
    result = inquirer.text(
        text, default=default, style=INQUIRER_STYLE, mandatory=mandatory, amark="✔", **kwargs
    ).execute()
    return result


def confirm(
    question: str = "Do you want to continue? [N/y]: ",
    values: List[str] = ["y", "Y", "yes", "Yes"],
) -> bool:
    # confirm action by user input

    confirm = input(question)
    if confirm not in values:
        return False
    return True

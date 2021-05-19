import inquirer

import src.cli.console as console


# input
def list(
    message,
    choices,
    message_no_choices="No choices available!",
):
    # choices exist
    if not len(choices) > 0:
        console.info(message_no_choices)
        return None

    # prompt
    questions = [
        inquirer.List(
            "select",
            message=message,
            choices=choices,
        ),
    ]
    answers = inquirer.prompt(questions)
    if not answers:
        return None

    return answers.get("select", None)

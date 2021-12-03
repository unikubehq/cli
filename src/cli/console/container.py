import src.cli.console as console


def container_list(data):
    if len(data.spec.containers) <= 1:
        return None

    container = console.list(
        message="Please select a container",
        message_no_choices="No container is running.",
        choices=[c.name for c in data.spec.containers],
    )
    if container is None:
        return None

    return container

from src.cli.console.input import exclude_by_identifier, resolve_duplicates


def test_input_resolve_duplicates():
    # with duplicates
    choices = ["choice", "choice"]
    identifiers = ["1", "2"]

    choices_resolved = resolve_duplicates(choices=choices, identifiers=identifiers)

    assert choices_resolved == ["choice (1)", "choice (2)"]

    # without duplicates
    choices = ["01", "02"]
    identifiers = ["1", "2"]

    choices_resolved = resolve_duplicates(choices=choices, identifiers=identifiers)

    assert choices_resolved == ["01", "02"]


def test_input_exclude_by_identifier():
    # exclude = None
    choices = ["choice", "choice"]
    identifiers = ["1", "2"]
    excludes = None

    choices_resolved = resolve_duplicates(choices=choices, identifiers=identifiers)
    choices_excluded = exclude_by_identifier(
        choices_display=choices_resolved, identifiers=identifiers, excludes=excludes
    )

    assert choices_excluded == ["choice (1)", "choice (2)"]

    # exclude existing
    choices = ["choice", "choice"]
    identifiers = ["1", "2"]
    excludes = ["1"]

    choices_resolved = resolve_duplicates(choices=choices, identifiers=identifiers)
    choices_excluded = exclude_by_identifier(
        choices_display=choices_resolved, identifiers=identifiers, excludes=excludes
    )

    assert choices_excluded == ["choice (2)"]

    # exclude non-existing
    choices = ["choice", "choice"]
    identifiers = ["1", "2"]
    excludes = ["3"]

    choices_resolved = resolve_duplicates(choices=choices, identifiers=identifiers)
    choices_excluded = exclude_by_identifier(
        choices_display=choices_resolved, identifiers=identifiers, excludes=excludes
    )

    assert choices_excluded == ["choice (1)", "choice (2)"]

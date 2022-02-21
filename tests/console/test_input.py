from unikube.cli.console.input import (
    exclude_by_identifiers,
    filter_by_identifiers,
    get_identifier_or_pass,
    resolve_duplicates,
)

CHOICE_01 = "choice (1)"
CHOICE_02 = "choice (2)"


class TestGetIdentifierOrPass:
    def test_with_identifier(self):
        selection = "NAME (IDENTIFIER)"
        selection = get_identifier_or_pass(selection=selection)
        assert selection == "IDENTIFIER"

    def test_without_identifier(self):
        selection = "NAME"
        selection = get_identifier_or_pass(selection=selection)
        assert selection == "NAME"


class TestResolveDuplicates:
    def test_with_duplicates(self):
        choices = ["choice", "choice"]
        identifiers = ["1", "2"]

        choices_resolved = resolve_duplicates(choices=choices, identifiers=identifiers)
        assert choices_resolved == [CHOICE_01, CHOICE_02]

    def test_without_duplicates(self):
        choices = ["01", "02"]
        identifiers = ["1", "2"]

        choices_resolved = resolve_duplicates(choices=choices, identifiers=identifiers)
        assert choices_resolved == ["01", "02"]

    def test_with_duplicates_and_help_text(self):
        choices = ["choice", "choice"]
        identifiers = ["1", "2"]
        help_texts = ["help", "help"]

        choices_resolved = resolve_duplicates(choices=choices, identifiers=identifiers, help_texts=help_texts)
        assert choices_resolved == ["choice (1) - help", "choice (2) - help"]

    def test_without_duplicates_and_help_text(self):
        choices = ["01", "02"]
        identifiers = ["1", "2"]
        help_texts = ["help", "help"]

        choices_resolved = resolve_duplicates(choices=choices, identifiers=identifiers, help_texts=help_texts)
        assert choices_resolved == ["01", "02"]

    def test_without_duplicates_and_help_text_always(self):
        choices = ["01", "02"]
        identifiers = ["1", "2"]
        help_texts = ["help", "help"]

        choices_resolved = resolve_duplicates(
            choices=choices, identifiers=identifiers, help_texts=help_texts, help_texts_always=True
        )
        assert choices_resolved == ["01 - help", "02 - help"]


class TestFilterByIdentifiers:
    def test_filter_none(self):
        choices = ["choice", "choice"]
        identifiers = ["1", "2"]
        filter_ = None

        choices_resolved = resolve_duplicates(choices=choices, identifiers=identifiers)
        choices_filtered = filter_by_identifiers(choices=choices_resolved, identifiers=identifiers, filter=filter_)
        assert choices_filtered == [CHOICE_01, CHOICE_02]

    def test_filter_empty_list(self):
        choices = ["choice", "choice"]
        identifiers = ["1", "2"]
        filter_ = []

        choices_resolved = resolve_duplicates(choices=choices, identifiers=identifiers)
        choices_filtered = filter_by_identifiers(choices=choices_resolved, identifiers=identifiers, filter=filter_)
        assert choices_filtered == []

    def test_filter_existing_01(self):
        choices = ["choice", "choice"]
        identifiers = ["1", "2"]
        filter_ = ["1"]

        choices_resolved = resolve_duplicates(choices=choices, identifiers=identifiers)
        choices_filtered = filter_by_identifiers(choices=choices_resolved, identifiers=identifiers, filter=filter_)
        assert choices_filtered == [CHOICE_01]

    def test_filter_existing_02(self):
        choices = ["different", "choice"]
        identifiers = ["1", "2"]
        filter_ = ["2"]

        choices_resolved = resolve_duplicates(choices=choices, identifiers=identifiers)
        choices_filtered = filter_by_identifiers(choices=choices_resolved, identifiers=identifiers, filter=filter_)
        assert choices_filtered == ["choice"]

    def test_filter_non_existing(self):
        choices = ["choice", "choice"]
        identifiers = ["1", "2"]
        filter_ = ["3"]

        choices_resolved = resolve_duplicates(choices=choices, identifiers=identifiers)
        choices_filtered = filter_by_identifiers(choices=choices_resolved, identifiers=identifiers, filter=filter_)
        assert choices_filtered == []


class TestExcludeByIdentifiers:
    def test_excludes_none(self):
        choices = ["choice", "choice"]
        identifiers = ["1", "2"]
        excludes = None

        choices_resolved = resolve_duplicates(choices=choices, identifiers=identifiers)
        choices_excluded = exclude_by_identifiers(choices=choices_resolved, identifiers=identifiers, excludes=excludes)
        assert choices_excluded == [CHOICE_01, CHOICE_02]

    def test_excludes_existing(self):
        choices = ["choice", "choice"]
        identifiers = ["1", "2"]
        excludes = ["1"]

        choices_resolved = resolve_duplicates(choices=choices, identifiers=identifiers)
        choices_excluded = exclude_by_identifiers(choices=choices_resolved, identifiers=identifiers, excludes=excludes)
        assert choices_excluded == [CHOICE_02]

    def test_excludes_non_existing(self):
        choices = ["choice", "choice"]
        identifiers = ["1", "2"]
        excludes = ["3"]

        choices_resolved = resolve_duplicates(choices=choices, identifiers=identifiers)
        choices_excluded = exclude_by_identifiers(choices=choices_resolved, identifiers=identifiers, excludes=excludes)
        assert choices_excluded == [CHOICE_01, CHOICE_02]

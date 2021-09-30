from src.cli.console.input import exclude_by_identifiers, filter_by_identifiers, resolve_duplicates


class TestResolveDuplicates:
    def test_with_duplicates(self):
        choices = ["choice", "choice"]
        identifiers = ["1", "2"]

        choices_resolved = resolve_duplicates(choices=choices, identifiers=identifiers)
        assert choices_resolved == ["choice (1)", "choice (2)"]

    def test_without_duplicates(self):
        choices = ["01", "02"]
        identifiers = ["1", "2"]

        choices_resolved = resolve_duplicates(choices=choices, identifiers=identifiers)
        assert choices_resolved == ["01", "02"]


class TestFilterByIdentifiers:
    def test_filter_none(self):
        choices = ["choice", "choice"]
        identifiers = ["1", "2"]
        filter = None

        choices_resolved = resolve_duplicates(choices=choices, identifiers=identifiers)
        choices_filtered = filter_by_identifiers(choices=choices_resolved, identifiers=identifiers, filter=filter)
        assert choices_filtered == ["choice (1)", "choice (2)"]

    def test_filter_empty_list(self):
        choices = ["choice", "choice"]
        identifiers = ["1", "2"]
        filter = []

        choices_resolved = resolve_duplicates(choices=choices, identifiers=identifiers)
        choices_filtered = filter_by_identifiers(choices=choices_resolved, identifiers=identifiers, filter=filter)
        assert choices_filtered == []

    def test_filter_existing_01(self):
        choices = ["choice", "choice"]
        identifiers = ["1", "2"]
        filter = ["1"]

        choices_resolved = resolve_duplicates(choices=choices, identifiers=identifiers)
        choices_filtered = filter_by_identifiers(choices=choices_resolved, identifiers=identifiers, filter=filter)
        assert choices_filtered == ["choice (1)"]

    def test_filter_existing_02(self):
        choices = ["different", "choice"]
        identifiers = ["1", "2"]
        filter = ["2"]

        choices_resolved = resolve_duplicates(choices=choices, identifiers=identifiers)
        choices_filtered = filter_by_identifiers(choices=choices_resolved, identifiers=identifiers, filter=filter)
        assert choices_filtered == ["choice"]

    def test_filter_non_existing(self):
        choices = ["choice", "choice"]
        identifiers = ["1", "2"]
        filter = ["3"]

        choices_resolved = resolve_duplicates(choices=choices, identifiers=identifiers)
        choices_filtered = filter_by_identifiers(choices=choices_resolved, identifiers=identifiers, filter=filter)
        assert choices_filtered == []


class TestExcludeByIdentifiers:
    def test_excludes_none(self):
        choices = ["choice", "choice"]
        identifiers = ["1", "2"]
        excludes = None

        choices_resolved = resolve_duplicates(choices=choices, identifiers=identifiers)
        choices_excluded = exclude_by_identifiers(choices=choices_resolved, identifiers=identifiers, excludes=excludes)
        assert choices_excluded == ["choice (1)", "choice (2)"]

    def test_excludes_existing(self):
        choices = ["choice", "choice"]
        identifiers = ["1", "2"]
        excludes = ["1"]

        choices_resolved = resolve_duplicates(choices=choices, identifiers=identifiers)
        choices_excluded = exclude_by_identifiers(choices=choices_resolved, identifiers=identifiers, excludes=excludes)
        assert choices_excluded == ["choice (2)"]

    def test_excludes_non_existing(self):
        choices = ["choice", "choice"]
        identifiers = ["1", "2"]
        excludes = ["3"]

        choices_resolved = resolve_duplicates(choices=choices, identifiers=identifiers)
        choices_excluded = exclude_by_identifiers(choices=choices_resolved, identifiers=identifiers, excludes=excludes)
        assert choices_excluded == ["choice (1)", "choice (2)"]

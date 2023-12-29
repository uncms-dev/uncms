import pytest

from tests.redirects.helpers import generate_csv
from uncms.redirects.importer import RedirectError, RedirectImporter
from uncms.redirects.models import Redirect


def test_redirecterror_str():
    error = RedirectError(filename="test.csv", line_number=5, message="badness")
    assert str(error) == "test.csv: 5: badness"


def test_redirectimporter_load():
    # Not skipping the header row should result in an error.
    importer = RedirectImporter()
    importer.load(
        generate_csv(
            [
                ("From", "To"),
                ("/example/", "/sample/"),
                ("/example2/", "/sample2/"),
                ("", ""),
                ("https://example.invalid/example3/", "/sample3/"),
            ]
        )
    )
    assert len(importer.errors) == 1
    assert importer.errors[0].line_number == 1
    assert (
        "must either be a full URL or start with a forward slash."
        in importer.errors[0].message
    )
    # But, make sure we've got the right things queued up in case someone
    # wants to ignore any errors.
    assert [(obj.old_path, obj.new_path) for obj in importer.to_create] == [
        ("/example/", "/sample/"),
        ("/example2/", "/sample2/"),
        ("/example3/", "/sample3/"),
    ]

    # Test the "old path is empty" branch.
    importer = RedirectImporter()
    importer.load(
        generate_csv(
            [
                ("/example/", "/sample/"),
                ("", "/sample/"),
                ("/example2/", "/sample2/"),
            ]
        )
    )
    assert len(importer.errors) == 1
    assert importer.errors[0].message == "Old path is empty at index 0."
    assert importer.errors[0].line_number == 2

    # Test the "not enough columns" branch.
    importer = RedirectImporter()
    importer.load(
        generate_csv(
            [
                ("/example/", "/sample/"),
                tuple(),
                ("/example2/", "/sample2/"),
            ]
        )
    )
    assert len(importer.errors) == 1
    assert importer.errors[0].message == "Expected 2 columns, found 0."
    assert importer.errors[0].line_number == 2

    # Test the "fails model validation" branch.
    importer = RedirectImporter()
    importer.load(
        generate_csv(
            [
                ("/example/", "/sample/"),
                ("example2/", "/sample/"),
            ]
        )
    )
    assert len(importer.errors) == 1
    assert "must either be a full URL" in importer.errors[0].message
    assert importer.errors[0].line_number == 2

    # Test a full CSV while skipping the header row. It should have no errors.
    importer = RedirectImporter()
    importer.load(
        generate_csv(
            [
                ("From", "To"),
                ("/example/", "/sample/"),
                ("/example2/", "/sample2/"),
                # allow totally empty lines
                ("", ""),
                # test domain normalisation while we're here...
                ("https://example.invalid/example3/", "/sample3/"),
            ]
        ),
        skip_header=True,
    )
    assert not importer.errors
    assert [(obj.old_path, obj.new_path) for obj in importer.to_create] == [
        ("/example/", "/sample/"),
        ("/example2/", "/sample2/"),
        ("/example3/", "/sample3/"),
    ]


@pytest.mark.django_db
def test_redirectimporter_save():
    importer = RedirectImporter()
    importer.load(
        generate_csv(
            [
                ("From", "To"),
                ("/example/", "/sample/"),
                ("/example2/", "/sample2/"),
                # allow totally empty lines
                ("", ""),
                # test domain normalisation while we're here...
                ("https://example.invalid/example3/", "/sample3/"),
            ]
        ),
        skip_header=True,
    )
    # Make sure that no redirects are created in dry-run mode.
    importer.save(dry_run=True)
    assert Redirect.objects.count() == 0

    # Test in not-dry-run mode.
    importer = RedirectImporter()
    importer.load(
        generate_csv(
            [
                ("/example/", "/sample/"),
                ("/example2/", "/sample2/"),
                ("https://example.invalid/example3/", "/sample3/"),
            ]
        )
    )
    importer.save()
    assert [(obj.old_path, obj.new_path) for obj in Redirect.objects.all()] == [
        ("/example/", "/sample/"),
        ("/example2/", "/sample2/"),
        ("/example3/", "/sample3/"),
    ]
    assert importer.statistics["created"] == 3
    assert importer.statistics["updated"] == 0
    assert importer.statistics["total"] == 3

    # Test that old redirects are updated.
    importer = RedirectImporter()
    importer.load(
        generate_csv(
            [
                ("/example/", "/sample5/"),
                ("/example2/", "/sample4/"),
            ]
        )
    )
    importer.save()
    assert [(obj.old_path, obj.new_path) for obj in Redirect.objects.all()] == [
        ("/example/", "/sample5/"),
        ("/example2/", "/sample4/"),
        ("/example3/", "/sample3/"),
    ]
    assert importer.statistics["created"] == 0
    assert importer.statistics["updated"] == 2

"""
This file implements CSVImporter, a class which assists with importing
redirects in batch mode from a CSV file. It is used in both a management
command and in an admin form.

Often when building out a new site of any size, it is useful to throw together
a shared spreadsheet of old URLs and new ones, and import them in a single
batch. I've probably implemented a dozen ad-hoc versions of this file in
various projects over the years, and almost all the rest probably *would* have
been used in all the others if it was present.

This could reasonably be implemented with django-import-export (an excellent
project), but this does exactly what it needs to do, and we don't really want
the extra dependency for something most sites will want.
"""

import csv
from dataclasses import dataclass, field

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from uncms.redirects.models import Redirect


@dataclass
class RedirectError:
    """
    RedirectError represents an error encountered while processing a CSV file.
    str()'ing a RedirectError should always return a sensible message.
    """

    filename: str
    line_number: int
    message: str

    def __str__(self):
        return f"{self.filename}: {self.line_number}: {self.message}"


@dataclass
class RedirectImporter:
    # List of `RedirectError`s found after `load()` was called.
    errors: list = field(default_factory=list)
    # List of unsaved Redirect objects after `load()` was called. We do *not*
    # call `save()` on these instances; it's just the most convenient way to
    # represent them.
    to_create: list = field(default_factory=list)
    # List of tuples of (instance, created) after `RedirectImporter.save()`
    # was called.
    saved_objects: list = field(default_factory=list)

    def load(self, fd, skip_header=False):
        """
        Load the given file and validate all entries within it (call `save()`
        after this to actually save it to the database).
        """
        reader = csv.reader(fd)
        for index, line in enumerate(reader):
            index_1 = index + 1
            if index == 0 and skip_header:
                continue

            if len(line) < 2:
                self.errors.append(
                    RedirectError(
                        filename=fd.name,
                        line_number=index_1,
                        message=_("Expected 2 columns, found {count}.").format(
                            count=len(line)
                        ),
                    )
                )
                continue

            # Allow lines with empty cells.
            if not any(line):
                continue

            old_path = line[0].strip()
            new_path = line[1].strip()

            # Give a more meaningful message if old_path is empty rather than
            # "this field is required" from model validation.
            if not old_path:
                self.errors.append(
                    RedirectError(
                        filename=fd.name,
                        line_number=index_1,
                        message=_("Old path is empty at index 0."),
                    )
                )
                continue
            try:
                temporary_obj = Redirect(old_path=old_path, new_path=new_path)
                temporary_obj.full_clean(validate_unique=False)
            except ValidationError as e:
                self.errors.append(
                    RedirectError(
                        filename=fd.name,
                        line_number=index_1,
                        message="; ".join(e.messages),
                    )
                )
            else:
                self.to_create.append(temporary_obj)

    def save(self, dry_run=False):
        with transaction.atomic():
            for redirect in self.to_create:
                self.saved_objects.append(
                    Redirect.objects.update_or_create(
                        defaults={"new_path": redirect.new_path},
                        old_path=redirect.old_path,
                    )
                )

            if dry_run:
                transaction.set_rollback(True)

    @property
    def statistics(self):
        return {
            "total": len(self.saved_objects),
            "created": len([obj for obj in self.saved_objects if obj[1] is True]),
            "updated": len([obj for obj in self.saved_objects if obj[1] is False]),
        }

from django.core.management import BaseCommand, CommandError
from django.utils.translation import gettext_lazy as _

from uncms.redirects.importer import RedirectImporter


class Command(BaseCommand):
    help = "Import redirects from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument("files", nargs="+")
        parser.add_argument(
            "--skip-header",
            action="store_true",
            default=False,
            help=_("skip first line of the file (if your CSV file has a header row)"),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help=_("don't save redirects; show what would have been done instead"),
        )
        parser.add_argument(
            "--ignore-errors",
            action="store_true",
            help=_("ignore bad entries and attempt to continue"),
        )

    def handle(self, *args, **options):
        importer = RedirectImporter()
        for f in options["files"]:
            with open(f, encoding="utf-8") as fd:
                importer.load(fd, skip_header=options["skip_header"])

        if importer.errors:
            for error in importer.errors:
                if options["ignore_errors"]:
                    style = self.style.WARNING
                else:
                    style = self.style.ERROR
                self.stderr.write(style(str(error)))
            if not options["ignore_errors"]:
                raise CommandError(
                    _(
                        "abandoning import due to errors (use `--ignore-errors` to skip bad entries)"
                    )
                )

        importer.save(dry_run=options["dry_run"])

        if options["dry_run"] or options["verbosity"] > 1:
            for obj, created in importer.saved_objects:
                if created:
                    message = _("created: {obj}").format(obj=str(obj))
                else:
                    message = _("updated: {obj}").format(obj=str(obj))
                if options["dry_run"]:
                    self.stdout.write(_("DRY RUN: {message}").format(message=message))
                else:  # we're printing because we're in super verbose mode
                    self.stdout.write(message)

        if options["dry_run"]:
            self.stdout.write(
                self.style.SUCCESS(
                    _(
                        "DRY RUN: {created} would have been created, {updated} would have been updated, {total} total"
                    ).format(**importer.statistics)
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    _(
                        "{created} redirects created, {updated} updated, {total} total"
                    ).format(**importer.statistics)
                )
            )

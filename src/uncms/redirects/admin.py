from django.contrib import admin, messages
from django.contrib.admin.options import IS_POPUP_VAR
from django.http import HttpResponseNotFound
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from uncms.conf import defaults
from uncms.redirects.forms import RedirectImportForm, RedirectImportSaveForm
from uncms.redirects.models import Redirect


@admin.register(Redirect)
class RedirectAdmin(admin.ModelAdmin):
    list_filter = ["type"]
    search_fields = ("old_path", "new_path")

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_import_button"] = (
            self.is_import_enabled(request)
            and
            # Don't show it when we're in a popup (if that's ever meaningful
            # here - likely nothing will ever have an FK to us).
            IS_POPUP_VAR not in request.GET
        )
        return super().changelist_view(request, extra_context)

    def is_import_enabled(self, request):
        return all(
            [
                # It's never enabled for anyone if REDIRECTS_CSV_IMPORT_ENABLED
                # is off.
                defaults.REDIRECTS_CSV_IMPORT_ENABLED,
                self.has_add_permission(request),
                # Change permission is required because if a redirect is found
                # in the CSV which already exists, it will be updated.
                self.has_change_permission(request),
            ]
        )

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj=obj)
        if not defaults.REGEX_REDIRECTS:
            fields.remove("regular_expression")
            fields.remove("test_path")
        return fields

    def get_list_display(self, request):
        if defaults.REGEX_REDIRECTS:
            return [
                "old_path",
                "new_path",
                "regular_expression",
                "type",
                "test_redirect",
            ]
        return ["old_path", "new_path", "type", "test_redirect"]

    def get_urls(self):
        """Adds in some custom admin URLs."""
        return [
            path(
                "import-csv/",
                self.admin_site.admin_view(self.import_csv_view),
                name="redirects_redirect_import_csv",
            ),
        ] + super().get_urls()

    @method_decorator(require_http_methods(["GET", "POST"]))
    def import_csv_view(self, request):
        if not self.is_import_enabled(request):
            return HttpResponseNotFound("Feature disabled.")

        template = "admin/redirects/redirect/import_form.html"
        base_context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
        }

        if request.method == "GET":
            return render(
                request,
                template,
                {
                    **base_context,
                    **{
                        "title": _("Import redirects from CSV"),
                        "form": RedirectImportForm(),
                    },
                },
            )

        if not request.POST.get("csv_data"):
            form = RedirectImportForm(request.POST, request.FILES)

            if not form.is_valid():
                # can't really happen, client-side validation should take care of
                # this, but...
                return render(
                    request,
                    template,
                    {
                        **base_context,
                        **{"title": _("Import redirects from CSV"), "form": form},
                    },
                )

            form.importer.save(dry_run=True)
            return render(
                request,
                template,
                {
                    **base_context,
                    **{
                        "title": _("Review import"),
                        "form": form,
                        "confirming": True,
                        "save_form": RedirectImportSaveForm(
                            initial={
                                "csv_data": form.cleaned_data["csv_file"].read(),
                                "filename": form.cleaned_data["csv_file"].name,
                            },
                        ),
                    },
                },
            )

        form = RedirectImportSaveForm(request.POST)
        if not form.is_valid():
            raise AssertionError("this should not happen")  # pragma: no cover
        # Once that data is valid, we can use the *other* form to save it
        # (this convolution is necessary because we can't persist file inputs
        # across requests)
        form.importer.save()
        messages.success(
            request,
            _("Import successful. {created} created, {updated} updated.").format(
                **form.importer.statistics
            ),
        )
        return redirect(reverse("admin:redirects_redirect_changelist"))

    @admin.display(description=_("Test"))
    def test_redirect(self, obj):
        if obj.regular_expression:
            url = obj.test_path
        else:
            url = obj.old_path
        return format_html(
            '<a target="_blank" rel="noopener noreferrer" href="{}">{}</a>',
            url,
            _("Test"),
        )

    class Media:
        # This JS will conditionally hide or show the "test path" field based
        # on the value of the "regular expression" field.
        js = ["uncms/js/redirect-fields.js"]

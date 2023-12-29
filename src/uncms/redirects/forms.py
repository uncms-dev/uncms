import io

from django import forms
from django.utils.translation import gettext_lazy as _

from uncms.redirects.importer import RedirectImporter


class RedirectImportForm(forms.Form):
    """
    A form for the CSV importer. This handles the initial "check over the file"
    """

    csv_file = forms.FileField(
        label=_("CSV file"),
    )

    def __init__(self, *args, **kwargs):
        self.importer = RedirectImporter()
        super().__init__(*args, **kwargs)

    def clean_csv_file(self):
        # `csv` can only work on text files, and we always get bytes from
        # FileField, and we cannot (reasonably, portably across temporary
        # storages) re-open in text mode
        try:
            wrapper = io.TextIOWrapper(self.cleaned_data["csv_file"])
            self.importer.load(wrapper)
            wrapper.seek(0)
        except UnicodeDecodeError as e:
            raise forms.ValidationError(
                "Decoding error - probably a binary file."
            ) from e
        return wrapper


class RedirectImportSaveForm(forms.Form):
    """
    A second form, with hidden inputs, used to save the form. This convolution
    is necessary because we cannot persist FileField across requests.
    """

    csv_data = forms.CharField(
        widget=forms.Textarea(attrs={"hidden": "hidden"}),
    )

    filename = forms.CharField(
        widget=forms.HiddenInput(),
    )

    def __init__(self, *args, **kwargs):
        self.importer = RedirectImporter()
        super().__init__(*args, **kwargs)

    def clean(self):
        fd = io.StringIO(self.cleaned_data["csv_data"])
        fd.name = self.cleaned_data["filename"]
        self.importer.load(fd)

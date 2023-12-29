from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class RedirectTypeChoices(TextChoices):
    PERMANENT = "301", _("Permanent")
    TEMPORARY = "302", _("Temporary")

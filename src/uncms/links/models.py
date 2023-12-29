from django.db import models
from django.utils.translation import gettext_lazy as _

from uncms.models import LinkField
from uncms.pages.models import ContentBase


class Link(ContentBase):
    """
    A redirect to another URL.
    """

    classifier = "utilities"

    icon = "links/img/link.png"

    urlconf = "uncms.links.urls"

    robots_index = False

    link_url = LinkField(
        verbose_name=_("link URL"),
        help_text=_("The URL where the user will be redirected."),
    )

    permanent_redirect = models.BooleanField(
        default=False,
        help_text=_(
            "By default, a temporary redirect (302) will be used. Check this option to use a permanent (301) redirect."
        ),
    )

    def __str__(self):
        return self.page.title

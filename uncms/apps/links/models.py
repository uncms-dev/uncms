from django.db import models
from django.utils.translation import gettext_lazy as _

from uncms.apps.pages.models import ContentBase
from uncms.models import LinkField


class Link(ContentBase):
    '''
    A redirect to another URL.
    '''

    classifier = 'utilities'

    icon = 'links/img/link.png'

    urlconf = 'uncms.apps.links.urls'

    robots_index = False

    link_url = LinkField(
        verbose_name=_('link URL'),
        help_text=_('The URL where the user will be redirected.'),
    )

    permanent_redirect = models.BooleanField(
        default=False,
        help_text=_('By default, a temporary redirect (302) will be used. Check this option to use a permanent (301) redirect.'),
    )

    def __str__(self):
        return self.page.title

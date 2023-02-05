import re
from functools import cached_property
from sre_constants import error as RegexError
from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.http import (
    HttpResponseGone,
    HttpResponsePermanentRedirect,
    HttpResponseRedirect,
)
from django.utils.translation import gettext_lazy as _

from uncms.conf import defaults
from uncms.redirects.types import RedirectTypeChoices


class RedirectManager(models.Manager):
    def get_for_path(self, path):
        if not defaults.REGEX_REDIRECTS:
            return Redirect.objects.filter(old_path=path).first()

        for redirect in self.all():
            if redirect.old_path == path and not redirect.regular_expression:
                return redirect
            if redirect.regular_expression and re.match(redirect.old_path, path):
                return redirect

        return None

    def get_queryset(self):
        # If regex redirects have been enabled at some point in time, then
        # turned off again for [reason], we don't want any regular expression
        # redirects to have any effect. And we can also simplify validation if
        # we can be sure that a redirect will never be a regular expression if
        # we have regular expressions disabled. So, always exclude regex
        # redirects if REGEX_REDIRECTS is off.
        queryset = super().get_queryset()
        if not defaults.REGEX_REDIRECTS:
            queryset = queryset.filter(regular_expression=False)
        return queryset


class Redirect(models.Model):
    objects = RedirectManager()

    type = models.CharField(
        max_length=3,
        choices=RedirectTypeChoices.choices,
        default=RedirectTypeChoices.PERMANENT,
    )

    old_path = models.CharField(
        _('redirect from'),
        max_length=200,
        db_index=True,
        unique=True,
        help_text=_('This can either be a whole URL, or just a path excluding the domain name (starting with "/"); it will be normalised to a path when you save. Example: "https://www.example.com/events/" or "/events/".'),
    )

    new_path = models.CharField(
        'redirect to',
        max_length=200,
        blank=True,
        help_text=_('If you leave this empty, a 410 Gone response will be served for this URL.'),
    )

    regular_expression = models.BooleanField(
        default=False,
        help_text=_(
            'This will allow using regular expressions to match and '
            'replace patterns in URLs. See the '
            '<a href="https://docs.python.org/3/library/re.html" rel="noopener noreferrer" target="_blank">Python '
            'regular expression documentation</a> for details.'
        ),
    )

    test_path = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text=_("You will need to specify a test path to ensure your regular expression is valid."),
    )

    class Meta:
        verbose_name = _('redirect')
        verbose_name_plural = _('redirects')
        ordering = ('old_path',)

    def __str__(self):
        if self.new_path:
            return f'{self.old_path} 🡢 {self.new_path}'
        return self.old_path

    def clean(self):
        super().clean()
        # Make sure regular expression redirects have a test path, and
        # validate that their regexes look something like regexes.
        if self.regular_expression:
            if not self.test_path:
                raise ValidationError({
                    'test_path': _('A test path is necessary to validate your regular expression.')
                })

            # Test compiling the old path separately. If an error occurs here
            # we can definitively attribute it to the "old_path field"...
            try:
                re.compile(self.old_path)
            except RegexError as err:
                raise ValidationError({
                    'old_path': _('There was an error in your regular expression: {}').format(str(err))
                }) from err
            # ...whereas if it happens in the `new_path` field we know it must
            # be a bad substitution in `new_path`.
            try:
                re.sub(self.old_path, self.new_path, self.test_path)
            except RegexError as err:
                raise ValidationError({
                    'new_path': _('There was an error in your substitution: {}').format(str(err))
                }) from err
        else:
            # On the "not regular expression" branch (because question marks
            # have a regex meaning): make sure they've not put a "?" in the
            # URL. It does not do what they think it does.
            if '?' in self.old_path:
                raise ValidationError({
                    'old_path': _(
                        "There appears to be a query string component in your old path. "
                        "This does not do what you are expecting; "
                        "redirects can only work on paths, not on query strings."
                    ),
                })
            # Allows pasting in whole URLs from a browser in the `old_path`
            # field, to make creating redirects less effort for users (they
            # can just copy-paste URLs from their browser). Normalise it to a
            # path on save.
            #
            # We do this on the "not a regular expression" branch because
            # regexes can contain all sorts of characters that may be mistaken
            # for URL components.
            parsed = urlparse(self.old_path)

            if parsed.netloc and parsed.scheme in ['http', 'https']:
                # A old_path like https://example.com (note lack of trailing slash)
                # is valid but the path part will be empty. Assume they mean
                # "/" if no path part is present.
                self.old_path = parsed.path

            if not self.old_path.startswith('/'):
                raise ValidationError({
                    'old_path': _('"From" path must either be a full URL or start with a forward slash.'),
                })

            # ...but that's not all! If the "new" path contains something in
            # ALLOWED_HOSTS, then it's almost certainly a local URL. Again, we
            # can be nice and normalise that for them, to allow pasting in
            # URLs from their browser.
            parsed = urlparse(self.new_path)
            if parsed.netloc and parsed.scheme in ['http', 'https'] and parsed.netloc in settings.ALLOWED_HOSTS:
                self.new_path = parsed._replace(scheme='', netloc='').geturl()

        # obvious sanity check - this is done down here because it must be
        # done *after* the domain-removal normalisation.
        if self.old_path == self.new_path:
            raise ValidationError({
                'old_path': _("New path must not be the same as the old one (you can't redirect something to itself)."),
            })

    @cached_property
    def permanent(self):
        return self.type == RedirectTypeChoices.PERMANENT

    def response_for_path(self, path):
        if self.new_path == '':
            return HttpResponseGone()
        if self.permanent:
            return HttpResponsePermanentRedirect(self.sub_path(path))
        return HttpResponseRedirect(self.sub_path(path))

    def sub_path(self, request_path):
        """
        `sub_path` substitutes the value in `request_path`.

        If this redirect is a regular expression, it will return a
        rewritten version of `request_path`; otherwise returns its own
        `new_path`.
        """
        if not self.regular_expression:
            return self.new_path
        return re.sub(self.old_path, self.new_path, request_path)

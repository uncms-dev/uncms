"""Abstract base models used by the page management application."""
from urllib.parse import urlencode, urlparse

from django.db import models
from django.shortcuts import render
from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils.translation import gettext_lazy as _
from watson.search import SearchAdapter

from uncms.conf import defaults
from uncms.media.fields import ImageRefField
from uncms.models.managers import (
    OnlineBaseManager,
    PageBaseManager,
    PublishedBaseManager,
    SearchMetaBaseManager,
)


class PathTokenGenerator:
    """
    PathTokenGenerator is a simple token generator that takes a path and
    generates a signed path for it. It allows adding reasonably-unguessable
    preview URLs to offline pages, as well as for signing image thumbnail
    URLs.
    """

    key_salt = "cms.apps.pages.models.base.PathTokenGenerator"

    def check_token(self, token, path):
        return constant_time_compare(
            token,
            salted_hmac(
                self.key_salt, path, secret=defaults.PATH_SIGNING_SECRET
            ).hexdigest()[::2],
        )

    def make_token(self, path):
        return salted_hmac(
            key_salt=self.key_salt,
            value=path,
            secret=defaults.PATH_SIGNING_SECRET,
        ).hexdigest()[::2]

    def make_url(self, path, token_parameter="preview"):
        parsed = urlparse(path)
        parsed = parsed._replace(
            query=urlencode({token_parameter: self.make_token(path)})
        )
        return parsed.geturl()


path_token_generator = PathTokenGenerator()


class PublishedBase(models.Model):

    """A model with publication controls."""

    objects = PublishedBaseManager()

    class Meta:
        abstract = True


class PublishedBaseSearchAdapter(SearchAdapter):

    """Base search adapter for PublishedBase derivatives."""

    def get_live_queryset(self):
        """Selects only live models."""
        return self.model.objects.all()


class OnlineBase(PublishedBase):
    objects = OnlineBaseManager()

    is_online = models.BooleanField(
        _("online"),
        default=True,
        help_text=_(
            "Uncheck this box to remove the page from the public website. "
            "Logged-in admin users will still be able to view this page by clicking the 'view on site' button."
        ),
    )

    def get_preview_url(self):
        # Not all derivatives of OnlineBase will have a URL.
        if not hasattr(self, "get_absolute_url"):
            return None  # pragma: no cover

        return path_token_generator.make_url(self.get_absolute_url())

    class Meta:
        abstract = True


class OnlineBaseSearchAdapter(PublishedBaseSearchAdapter):

    """Base search adapter for OnlineBase derivatives."""


class SearchMetaBase(OnlineBase):

    """Base model for models used to generate a standalone HTML page."""

    objects = SearchMetaBaseManager()

    # SEO fields.

    browser_title = models.CharField(
        max_length=1000,
        blank=True,
        help_text=_(
            "The heading to use in the user's web browser. "
            "Leave blank to use the page title. "
            "Search engines pay particular attention to this attribute."
        ),
    )

    meta_description = models.TextField(
        _("description"),
        blank=True,
        help_text=_("A brief description of the contents of this page."),
    )

    sitemap_priority = models.FloatField(
        _("priority"),
        choices=(
            (1.0, "Very high"),
            (0.8, "High"),
            (0.5, "Medium"),
            (0.3, "Low"),
            (0.0, "Very low"),
        ),
        default=None,
        blank=True,
        null=True,
        help_text=_(
            "The relative importance of this content on your site. Search engines use this "
            "as a hint when ranking the pages within your site."
        ),
    )

    sitemap_changefreq = models.IntegerField(
        _("change frequency"),
        choices=(
            (1, _("Always")),
            (2, _("Hourly")),
            (3, _("Daily")),
            (4, _("Weekly")),
            (5, _("Monthly")),
            (6, _("Yearly")),
            (7, _("Never")),
        ),
        default=None,
        blank=True,
        null=True,
        help_text=_(
            "How frequently you expect this content to be updated. "
            "Search engines use this as a hint when scanning your site for updates."
        ),
    )

    robots_index = models.BooleanField(
        _("allow indexing"),
        default=True,
        help_text=_(
            "Uncheck to prevent search engines from indexing this page. "
            "Do this only if the page contains information which you do not wish "
            "to show up in search results."
        ),
    )

    robots_follow = models.BooleanField(
        _("follow links"),
        default=True,
        help_text=_(
            "Uncheck to prevent search engines from following any links they find in this page. "
            "Do this only if the page contains links to other sites that you do not wish to "
            "publicise."
        ),
    )

    robots_archive = models.BooleanField(
        _("allow archiving"),
        default=True,
        help_text=_(
            "Uncheck this to prevent search engines from archiving this page. "
            "Do this this only if the page is likely to change on a very regular basis. "
        ),
    )

    # Open Graph fields
    og_title = models.CharField(
        verbose_name=_("title"),
        blank=True,
        max_length=100,
        help_text=_(
            "Title that will appear on social media posts. This is limited to 100 characters, "
            "but Facebook will truncate the title to 88 characters."
        ),
    )

    og_description = models.TextField(
        verbose_name=_("description"),
        blank=True,
        max_length=300,
        help_text=_(
            "Description that will appear on social media posts. It is limited to 300 "
            "characters, but it is recommended that you do not use anything over 200."
        ),
    )

    og_image = ImageRefField(
        verbose_name=_("image"),
        blank=True,
        null=True,
        help_text=_(
            "The recommended image size is 1200x627 (1.91:1 ratio); this gives you a big "
            "stand out thumbnail. Using an image smaller than 400x209 will give you a "
            "small thumbnail and will splits posts into 2 columns. "
            "If you have text on the image make sure it is centered."
        ),
    )

    def get_context_data(self):
        """Returns the SEO context data for this page."""
        title = str(self)
        # Return the context.
        return {
            "meta_description": self.meta_description,
            "robots_index": self.robots_index,
            "robots_archive": self.robots_archive,
            "robots_follow": self.robots_follow,
            "title": self.browser_title or title,
            "header": title,
            "og_title": self.og_title,
            "og_description": self.og_description,
            "og_image": self.og_image,
        }

    def render(self, request, template, context=None, **kwargs):
        """Renders a template as a HttpResponse using the context of this page."""
        page_context = self.get_context_data()
        page_context.update(context or {})
        return render(request, template, page_context, **kwargs)

    class Meta:
        abstract = True


class SearchMetaBaseSearchAdapter(OnlineBaseSearchAdapter):

    """Search adapter for SearchMetaBase derivatives."""

    def get_description(self, obj):
        """Returns the meta description."""
        return obj.meta_description

    def get_live_queryset(self):
        """Selects only live models."""
        return super().get_live_queryset().filter(robots_index=True)


class PageBase(SearchMetaBase):

    """
    An enhanced SearchMetaBase with a sensible set of common features suitable for
    most pages.
    """

    objects = PageBaseManager()

    # Base fields.

    slug = models.SlugField(
        max_length=150,
        help_text=_(
            "A unique portion of the URL that is used to identify this "
            "specific page using human-readable keywords (e.g., about-us)"
        ),
    )

    title = models.CharField(
        max_length=1000,
    )

    def __str__(self):  # pylint:disable=invalid-str-returned
        return self.title

    def get_context_data(self):
        """
        Returns the SEO context data for this page.
        """
        context_data = super().get_context_data()
        context_data.update(
            {
                "title": self.browser_title or self.title,
                "header": self.title,
            }
        )
        return context_data

    class Meta:
        abstract = True


class PageBaseSearchAdapter(SearchMetaBaseSearchAdapter):

    """Search adapter for PageBase derivatives."""

    def get_title(self, obj):
        """Returns the title of the page."""
        return obj.title

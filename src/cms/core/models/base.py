"""Abstract base models used by the page management application."""

from django.conf import settings
from django.db import models
from django.shortcuts import render

from cms.core import debug
from cms.core.optimizations import cached_getter
from cms.core.models.managers import PublishedModelManager, publication_manager
from cms.core.models.fields import NullBooleanField, EnumField


class PublishedModel(models.Model):
    
    """A model with publication controls."""
    
    objects = PublishedModelManager()
    
    @classmethod
    def select_published(cls, queryset):
        """
        Filters out unpublished objects from the given queryset.
        
        This method will automatically be applied to all querysets of this model
        when in an active publication context.
        
        Subclasses can override this method to define additinal publication
        rules.
        """
        return queryset.filter(is_online=True)
    
    def __init__(self, *args, **kwargs):
        """Initializes the PublishedModel."""
        super(PublishedModel, self).__init__(*args, **kwargs)
        # Add a flag to determine whether the publication manager was active.
        self._select_published_active = publication_manager.select_published_active()
    
    date_created = models.DateTimeField(auto_now_add=True)
    
    date_modified = models.DateTimeField("last modified",
                                         auto_now=True)
    
    is_online = models.BooleanField(
        "online",
        default = True,
        help_text = (
            "Uncheck this box to remove the page from the public website. "
            "Logged-in admin users will still be able to view this page by clicking the 'view on site' button."
        )
    )
    
    class Meta:
        abstract = True
    

class PageBase(PublishedModel):
    
    """
    Base model for models used to generate a HTML page.
    
    This class is suited to pages that are to be included in feed-based views.
    For permanent or semi-permanent fixtures in a site, use the PageBase model
    instead.
    """
    
    # Hierarchy fields.
    
    parent = None
    
    @property
    def all_parents(self):
        """A list of all parents of this page."""
        if self.parent:
            return [self.parent] + self.parent.all_parents
        return []

    @property
    def breadcrumbs(self):
        """The breadcrumb trail for this page, including this page."""
        parents = self.all_parents
        parents.reverse()
        parents.append(self)
        return parents
        
    children = ()
    
    @property
    def all_children(self):
        """All the children of this page, cascading down to their children too."""
        children = []
        for child in self.children:
            children.append(child)
            children.extend(child.all_children)
        return children
    
    @property
    def navigation(self):
        """The navigation entries underneath this page."""
        return self.children
    
    @property
    def siblings(self):
        """All sibling pages in the hierarchy."""
        if self.parent:
            return self.parent.children
        return ()
        
    @property
    @cached_getter
    @debug.print_exc
    def next(self):
        """The next sibling, according to the default child ordering, or None."""
        sibling_iter = iter(self.siblings)
        while True:
            try:
                sibling = sibling_iter.next()
                if sibling == self:
                    return sibling_iter.next()
            except StopIteration:
                break
        return None
        
    @property
    @cached_getter
    @debug.print_exc
    def prev(self):
        """The previous sibling, according to the default child ordering, or None."""
        sibling_iter = iter(reversed(self.siblings))
        while True:
            try:
                sibling = sibling_iter.next()
                if sibling == self:
                    return sibling_iter.next()
            except StopIteration:
                break
        return None
    
    # Base fields.
    
    url_title = models.SlugField("URL title",
                                 db_index=False)
    
    title = models.CharField(
        max_length = 1000,
    )
    
    # Navigation fields.
    
    short_title = models.CharField(
        max_length = 200,
        blank = True,
        help_text = (
            "A shorter version of the title that will be used in site navigation. "
            "Leave blank to use the full-length title."
        ),
    )
    
    # SEO fields.
    
    browser_title = models.CharField(
        max_length = 1000,
        blank = True,
        help_text = (
            "The heading to use in the user's web browser. "
            "Leave blank to use the page title. "
            "Search engines pay particular attention to this attribute."
        )
    )
    
    meta_keywords = models.CharField("keywords",
                                     max_length=1000,
                                     blank=True,
                                     help_text="A comma-separated list of keywords for this page. Use this to specify common mis-spellings or alternative versions of important words in this page.")

    meta_description = models.TextField("description",
                                        blank=True,
                                        help_text="A brief description of the contents of this page.")
    
    sitemap_priority = models.FloatField("priority",
                                         choices=settings.SEO_PRIORITIES,
                                         default=None,
                                         blank=True,
                                         null=True,
                                         help_text="The relative importance of this content in your site.  Search engines use this as a hint when ranking the pages within your site.")

    sitemap_changefreq = EnumField("change frequency",
                                   choices=((1, "always", "Always"),
                                            (2, "hourly", "Hourly"),
                                            (3, "daily", "Daily"),
                                            (4, "weekly", "Weekly"),
                                            (5, "monthly", "Monthly"),
                                            (6, "yearly", "Yearly"),
                                            (7, "never", "Never")),
                                   default=None,
                                   blank=True,
                                   null=True,
                                   help_text="How frequently you expect this content to be updated.  Search engines use this as a hint when scanning your site for updates.")
    
    robots_index = NullBooleanField("allow indexing",
                                    blank=True,
                                    default=None,
                                    help_text="Use this to prevent search engines from indexing this page. Disable this only if the page contains information which you do not wish to show up in search results. Leave blank to use the setting from the parent page.")

    robots_follow = NullBooleanField("follow links",
                                     blank=True,
                                     default=None,
                                     help_text="Use this to prevent search engines from following any links they find in this page. Disable this only if the page contains links to other sites that you do not wish to publicise. Leave blank to use the setting from the parent page.")

    robots_archive = NullBooleanField("allow archiving",
                                      blank=True,
                                      default=None,
                                      help_text="Use this to prevent search engines from archiving this page. Disable this only if the page is likely to change on a very regular basis. Leave blank to use the setting from the parent page.")
    
    def resolve_meta_robots(self, index=None, follow=None, archive=None):
        """
        Returns the appropriate meta robots to be used for this page.
        
        The returned value is a tuple of (index, follow, archive).
        """
        page = self
        while page and (index is None or archive is None or follow is None):
            if index is None:
                index = page.robots_index
            if archive is None:
                archive = page.robots_archive
            if follow is None:
                follow = page.robots_follow
            page = page.parent
        return index, follow, archive
    
    def get_context_data(self):
        """Returns the SEO context data for this page."""
        robots_index, robots_follow, robots_archive = self.resolve_meta_robots()
        # Return the context.
        return {
            "meta_description": self.meta_description,
            "meta_keywords": self.meta_keywords,
            "robots_index": robots_index,
            "robots_archive": robots_archive,
            "robots_follow": robots_follow,
            "title": self.browser_title or self.title,
            "header": self.title
        }
    
    def render(self, request, template, context=None, **kwargs):
        """Renders a template as a HttpResponse using the context of this page."""
        page_context = self.get_context_data()
        page_context.update(context or {})
        return render(request, template, page_context, **kwargs)
    
    # Base model methods.
    
    def __unicode__(self):
        """
        Returns the short title of this page, falling back to the standard
        title.
        """
        return self.short_title or self.title
    
    class Meta:
        abstract = True
        ordering = ("title",)


"""Core models used by the CMS."""


import datetime

from django import forms, template
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.db import models
from django.db.models.base import ModelBase
from django.http import Http404
from django.shortcuts import render_to_response

from cms.apps.pages import content
from cms.apps.pages.forms import HtmlWidget
from cms.apps.pages.optimizations import cached_getter, cached_setter


PAGE_PUBLICATION_SQL = """
    is_online = TRUE AND
    (
        (
            publication_date <= NOW()
        ) AND
        (
            expiry_date IS NULL OR
            expiry_date > NOW()
        )
    )
"""


class PageBaseManager(models.Manager):
    
    """
    Base manager for all pages.
    
    This must be subclassed when creating managers for Page subclasses.
    """
    
    use_for_related_fields = True
    
    def get_query_set(self):
        """Adds the is_published property to all loaded pages."""
        queryset = super(PageBaseManager, self).get_query_set()
        queryset = queryset.filter(site=Site.objects.get_current())
        queryset = queryset.extra(select={"is_published": PAGE_PUBLICATION_SQL})
        return queryset


class PublishedPageManager(PageBaseManager):
    
    """Manager that selects only published pages."""
    
    use_for_related_fields = False
    
    def select_published(self, queryset):
        """Filters out unpublished objects from the queryset."""
        return queryset.extra(where=[PAGE_PUBLICATION_SQL])
    
    def get_query_set(self):
        """Returns the filtered query set."""
        queryset = super(PublishedPageManager, self).get_query_set()
        queryset = self.select_published(queryset)
        return queryset
  
  
class PageBase(models.Model):
    
    """Base model for models used to generate a HTML page."""
    
    # Model management.
    
    objects = PageBaseManager()
    
    published_objects = PublishedPageManager()
        
    # Base fields.
    
    last_modified = models.DateTimeField(auto_now=True)
    
    site = models.ForeignKey(Site,
                             default=Site.objects.get_current,
                             editable=False)
    
    title = models.CharField(max_length=1000)
    
    url_title = models.SlugField("URL title")
    
    # Publication fields.
    
    is_online = models.BooleanField("online",
                                    default=True,
                                    help_text="Uncheck this box to remove the page from the public website.  Logged-in admin users will still be able to view this page by directly visiting it's URL.")
    
    publication_date = models.DateTimeField(default=datetime.datetime.now,
                                            help_text="The date that this page will appear on the website.  Leave this blank to immediately publish this page.")

    expiry_date = models.DateTimeField(blank=True,
                                       null=True,
                                       help_text="The date that this page will be removed from the website.  Leave this blank to never expire this page.")
    
    # Navigation fields.
    
    short_title = models.CharField(max_length=100,
                                   blank=True,
                                   null=True,
                                   help_text="A shorter version of the title that will be used in site navigation. Leave blank to use the full-length title.")
    
    # SEO fields.
    
    browser_title = models.CharField(max_length=1024,
                                     blank=True,
                                     null=True,
                                     help_text="The heading to use in the user's web browser.  Leave blank to use the page title.  Search engines pay particular attention to this attribute.")
    
    meta_keywords = models.CharField("keywords",
                                     max_length=1024,
                                     blank=True,
                                     null=True,
                                     help_text="A comma-separated list of keywords for this page. Use this to specify common mis-spellings or alternative versions of important words in this page.")

    meta_description = models.TextField("description",
                                        blank=True,
                                        null=True,
                                        help_text="A brief description of the contents of this page. Leave blank to use to use the parent page description.")
    
    sitemap_priority = models.FloatField("priority",
                                         choices=settings.SEO_PRIORITIES,
                                         default=settings.SEO_DEFAULT_PRIORITY,
                                         blank=True,
                                         null=True,
                                         help_text="The relative importance of this content in your site.  Search engines use this as a hint when ranking the pages within your site.")
    
    sitemap_changefreq = models.CharField("change frequency",
                                          max_length=255,
                                          choices=settings.SEO_CHANGE_FREQUENCIES,
                                          default=settings.SEO_DEFAULT_CHANGE_FREQUENCY,
                                          blank=True,
                                          null=True,
                                          help_text="How frequently you expect this content to be updated.  Search engines use this as a hint when scanning your site for updates.")
    
    robots_index = models.BooleanField("allow indexing",
                                        default=True,
                                        help_text="Uncheck this box to prevent search engines from indexing this page. Disable this only if the page contains information which you do not wish to show up in search results.")

    robots_archive = models.BooleanField("allow archiving",
                                         default=True,
                                         help_text="Uncheck this box to prevent search engines from archiving this page. Disable this only if the page is likely to change on a very regular basis.")

    robots_follow = models.BooleanField("follow links",
                                        default=True,
                                        help_text="Uncheck this box to prevent search engines from following any links they find in this page. Disable this only if the page contains links to other sites that you do not wish to publicise.")

    # Page rendering methods.
    
    def render_to_response(self, request, template_name, context, **kwargs):
        """Renders the given template using the given context."""
        # Check for publication state.
        if not self.is_published:
            if not (request.user.is_authenticated() and request.user.is_staff and request.user.is_active):
                raise Http404, "The page '%s' has not been published yet." % self
        # Parse context variables.
        breadcrumbs = request.breadcrumbs
        homepage = breadcrumbs[0]
        # Parse the main section.
        if len(breadcrumbs) > 1:
            section = breadcrumbs[1]
            nav_secondary = section.content.navigation
        else:
            section = None
            nav_secondary = None
        # Parse the subsection.
        if len(breadcrumbs) > 2:
            subsection = breadcrumbs[2]
            nav_tertiary = subsection.content.navigation
        else:
            subsection = None
            nav_tertiary = None
        # Generate the context.
        context.setdefault("page", self)
        context.setdefault("title", self.title)
        context.setdefault("short_title", context["title"])
        context.setdefault("browser_title", self.browser_title or context["title"])
        context.setdefault("meta_description", self.meta_description or homepage.meta_description)
        context.setdefault("meta_keywords", self.meta_keywords or homepage.meta_keywords)
        context.setdefault("robots_index", self.robots_index)
        context.setdefault("robots_archive", self.robots_archive)
        context.setdefault("robots_follow", self.robots_follow)
        context.setdefault("homepage", homepage)
        context.setdefault("is_homepage", (self == homepage))
        context.setdefault("site_title", homepage.browser_title or homepage.title)
        context.setdefault("robots_index", self.robots_index)
        context.setdefault("nav_primary", homepage.content.navigation)
        context.setdefault("section", section)
        context.setdefault("nav_secondary", nav_secondary)
        context.setdefault("subsection", subsection)
        context.setdefault("nav_tertiary", nav_tertiary)
        return render_to_response(template_name, context, template.RequestContext(request), **kwargs)
    
    # Base model methods.
    
    def get_absolute_url(self):
        """All pages must publish an absolute URL."""
        raise NotImplemented
    
    url = property(lambda self: self.get_absolute_url(),
                   doc="The absolute URL of the page.")
    
    def __unicode__(self):
        """
        Returns the short title of this page, falling back to the standard
        title.
        """
        return self.short_title or self.title
    
    class Meta:
        abstract = True
        ordering = ("title",)


class PageField(models.ForeignKey):
    
    """A foreign key to a Page model."""
    
    def __init__(self, to, content_type=None, limit_choices_to=None, **kwargs):
        """Initializes the Page Field."""
        # Generate the page filter.
        if content_type is not None:
            limit_choices_to = limit_choices_to or {}
            limit_choices_to.setdefault("content_type", content_type)
        # Initialize the PageField.
        super(PageField, self).__init__(to=to, limit_choices_to=limit_choices_to, default=self.get_default, **kwargs)
        
    def get_default(self):
        """Returns the default page."""
        try:
            return self.rel.to._default_manager.filter(**self.rel.limit_choices_to)[0].pk
        except IndexError:
            return None


class HtmlField(models.TextField):
    
    """A field that contains HTML data."""
    
    def formfield(self, **kwargs):
        """Returns a HtmlWidget."""
        kwargs["widget"] = HtmlWidget
        return super(HtmlField, self).formfield(**kwargs)


class PageManager(PageBaseManager):
    
    """Manager for Page objects."""
    
    def get_homepage(self):
        """Returns the site homepage."""
        return self.get(parent=None)


class ContentRegistrationError(Exception):
    
    """Exception raised when content registration goes wrong."""


class PageMetaClass(ModelBase):
    
    """Metaclass for Page models."""
    
    def __init__(self, name, bases, attrs):
        """Initializes the PageMetaClass."""
        super(PageMetaClass, self).__init__(name, bases, attrs)
        self.content_registry = {}
        self.register_content(content.Content, content.DEFAULT_CONTENT_SLUG)

    def register_content(self, content_cls, slug=None):
        """
        Registers the given content type with this class under the given slug.
        """
        slug = slug or content_cls.__name__.lower()
        self.content_registry[slug] = content_cls
      
    def unregister_content(self, slug):
        """Unregisters the content type associated with the given slug."""
        try:
            del self.content_registry[slug]
        except KeyError:
            raise ContentRegistrationError, "No content type is registered under %r." % slug
    
    def lookup_content(self, slug):
        """Looks up the given content type by type slug."""
        try:
            return self.content_registry[slug]
        except KeyError:
            raise ContentRegistrationError, "No content type is registered under %r." % slug


class Page(PageBase):

    """A page within the site."""

    __metaclass__ = PageMetaClass

    objects = PageManager()
    
    # Hierarchy fields.

    parent = PageField("self",
                       blank=True,
                       null=True)

    def get_all_parents(self):
        """Returns a list of all parents of this page."""
        if self.parent:
            return [self.parent] + self.parent.all_parents
        return []
    
    all_parents = property(get_all_parents,
                           doc="A list of all parents of this page.")

    order = models.PositiveSmallIntegerField(unique=True,
                                             editable=False,
                                             blank=True,
                                             null=True)

    @cached_getter
    def get_children(self):
        """
        Returns all the children of this page, regardless of their publication
        state.
        """
        return self.page_set.all().order_by("order")
    
    children = property(get_children,
                        doc="All children of this page.")
    
    def get_all_children(self):
        """
        Returns all the children of this page, cascading down to their children
        too.
        """
        children = []
        for child in self.children:
            children.append(child)
            children.extend(child.all_children)
        return children
            
    all_children = property(get_all_children,
                            doc="All the children of this page, cascading down to their children too.")
    
    @cached_getter
    def get_published_children(self):
        """Returns all the published children of this page."""
        return self.__class__.published_objects.select_published(self.children)

    published_children = property(get_published_children,
                                  doc="All the published children of this page.")

    # Navigation fields.

    in_navigation = models.BooleanField("add to navigation",
                                        default=True,
                                        help_text="Uncheck this box to remove this content from the site navigation.")

    @cached_getter
    def get_navigation(self):
        """
        Returns all published children that should be added to the navigation.
        """
        return self.published_children.filter(in_navigation=True)
        
    navigation = property(get_navigation,
                          doc="All published children that should be added to the navigation.")

    # Content fields.
    
    content_type = models.CharField(max_length=20,
                                    editable=False,
                                    help_text="The type of page content.")

    content_data = models.TextField(editable=False,
                                    help_text="The encoded data of this page.")
    
    @cached_getter
    def get_content(self):
        """Returns the content object associated with this page."""
        if not self.content_type:
            return None
        content_cls = self.__class__.lookup_content(self.content_type)
        content_instance = content_cls(self)
        return content_instance

    @cached_setter(get_content)
    def set_content(self, content):
        """Sets the content object for this page."""
        self.content_data = content.serialized_data

    content = property(get_content,
                       set_content,
                       doc="The content object associated with this page.")

    # Standard model methods.
    
    def get_absolute_url(self):
        """Generates the absolute url of the page."""
        if self.parent:
            return self.parent.url + self.url_title + "/"
        return reverse("render_homepage")
    
    class Meta:
        unique_together = (("parent", "url_title",),)


# Add some base content types.
    
       
Page.register_content(content.Redirect)

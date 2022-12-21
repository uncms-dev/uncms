'''Base classes for UnCMS ModelAdmins.'''
from django.contrib import admin
from django.db.models import Q
from django.db.models.deletion import get_candidate_relations_to_delete
from django.db.utils import DEFAULT_DB_ALIAS
from django.urls import NoReverseMatch, reverse
from django.utils.translation import gettext_lazy as _
from reversion.admin import VersionAdmin
from watson.admin import SearchAdmin

from uncms.conf import defaults
from uncms.models.base import (
    PageBaseSearchAdapter,
    SearchMetaBaseSearchAdapter,
)
from uncms.pages.models import Page


def check_inline_for_admin_url(obj, inline, parent, inline_check=True):
    """
    A function used to get the admin URL for an inline obj.

    Takes the object itself, an inline object and the class of the
    parent model.

    If no change URL is found, None is returned.
    """
    # We obviously need the object to be the same type of object
    # as the inline's parent to at least get anywhere useful. We
    # catch thisstraight away and immediately return if so to save
    # time.

    if inline_check and not isinstance(obj, inline.model):
        return None

    # We've got an inline for this model. Lets check the fk_name
    # attribute on the InlineModelAdmin. If it's set we'll use
    # that, else we'll find the ForeignKey to the parent.

    obj_fk_name = getattr(inline, 'fk_name', False)
    if obj_fk_name:
        # the fk_name value is set so we assume that it will
        # resolve a parent since an inline can't be saved without
        # a parent.

        obj_parent = getattr(obj, obj_fk_name, False)
        try:
            return reverse(
                f'admin:{obj_parent._meta.app_label}_{obj_parent._meta.model_name}_change',
                args=[obj_parent.pk]
            )
        except NoReverseMatch:
            pass

    # If we make it here, the fk_name attribute was not set or the
    # parent did not resolve to an object We'll now look for
    # specifically ForeignKeys to the parent model. There can't be
    # more than one as if there were, Django would throw errors on
    # inline registration due to the lack of the fk_name
    # attribute to distinguish the two fields.

    for field in obj._meta.get_fields():
        if field.get_internal_type() in ['ForeignKey', 'OneToOneField']:
            # Follow the ForeignKey to find the related model.

            related_model = obj._meta.get_field(field.attname).remote_field.model

            if parent == related_model:
                # We've found a Foreign key to the parent, now
                # to extract the page and get its admin change URL.

                try:
                    field_value = getattr(obj, field.attname)
                except AttributeError:
                    field_value = None

                if field_value:
                    return reverse(
                        f'admin:{related_model._meta.app_label}_{related_model._meta.model_name}_change',
                        args=[field_value]
                    )

    return None


def get_admin_url(obj):
    """
    Guesses the admin URL for an object.

    If the object has its own change view, then that will be returned.

    It will then check to see if it is an inline on another object's
    change view.

    Failing that, it will see if it is an inline registered to a Page
    (with page_admin.register_content_inline).
    """
    # Import here to avoid circular imports
    from uncms.pages.admin import page_admin  # pylint:disable=import-outside-toplevel,cyclic-import

    # We first of all just try and get an admin URL for the object that has
    # been passed to us.
    try:
        return reverse(
            f'admin:{obj._meta.app_label}_{obj._meta.model_name}_change',
            args=[obj.pk]
        )
    except NoReverseMatch:
        pass

    # If we can't get and admin change URL for the object directly, we'll
    # now see if it's an inline with a parent model. If so, we'll return
    # the parent model's change URL
    # Having been given an arbitrary object, the only way we can work explicitly
    # out what the object's parent is, without making any assumptions, is by
    # looking through all registered models and tunneling down.

    for model_cls, model_admin in admin.site._registry.items():
        # Check if the model we're looking at has any inlines. If it hasn't had
        # any inlines set, model.inlines returns an empty array.
        inlines = model_admin.inlines

        # Loop over the model's inlines and check for references to our obj
        for inline in inlines:
            url = check_inline_for_admin_url(obj, inline, model_cls)

            if url:
                return url

    # If we've made it here, then obj is neither an object with an admin
    # change URL nor is it an inline of a registered model with an admin
    # change URL. Lets check inlines registered with page_admin.
    for _ignore, inline in page_admin.content_inlines:
        # page_admin.content_inlines is a list of tuples. The first value
        # is the ContentType and the second is the inline InlineModelAdmin
        # used to register the model.
        # We're going to check for ForeignKeys to 'pages.Page' since they'll
        # have to have one to be registered as a content inline.

        url = check_inline_for_admin_url(obj, inline, Page)

        if url:
            return url

    # If none of the above work then we're really out of options. Just
    # return None and let our caller handle this.
    return check_inline_for_admin_url(obj, None, Page, inline_check=False)


def get_related_objects_admin_urls(obj):
    related_objs = []

    for related in get_candidate_relations_to_delete(obj._meta):
        related_objs = related_objs + list(related.related_model._base_manager.using(DEFAULT_DB_ALIAS).filter(
            **{"%s__in" % related.field.name: [obj]}
        ))

    return [
        {
            'title': str(obj),
            'model_name': obj._meta.verbose_name,
            'admin_url': get_admin_url(obj),
        } for obj in related_objs
    ]


class SEOQualityControlFilter(admin.SimpleListFilter):
    '''
    A filter for models deriving from SearchMetaBase, to find pages with
    incomplete SEO, OpenGraph or Twitter card information.

    Usage:

    class MyModelAdmin(SearchMetaBaseAdmin):
        list_filter = [SEOQualityControlFilter]
    '''

    title = _('quality control')

    parameter_name = 'seo_quality_control'

    def lookups(self, request, model_admin):
        return (
            ('no-meta-description', _('No meta description')),
            ('no-browser-title', _('No browser title')),
            ('incomplete-opengraph-fields', _('Incomplete Open Graph fields')),
            ('no-og-image', _('No Open Graph image')),
            ('incomplete-twitter-fields', _('Incomplete Twitter card fields')),
        )

    def queryset(self, request, queryset):
        if not self.value():
            return queryset

        options = {
            'no-meta-description': lambda qs: qs.filter(meta_description=''),
            'no-browser-title': lambda qs: qs.filter(browser_title=''),
            'incomplete-opengraph-fields': lambda qs: qs.filter(Q(og_description='') | Q(og_image=None)),
            'no-og-image': lambda qs: qs.filter(og_image=None),
            'incomplete-twitter-fields': lambda qs: qs.filter(Q(twitter_description='') | Q(Q(og_image=None) & Q(twitter_image=None))),
        }

        return options[self.value()](queryset)


class PublishedBaseAdmin(admin.ModelAdmin):
    '''Base admin class for models with publication controls.'''

    def view_on_site(self, obj):
        return obj.get_preview_url()


class OnlineBaseAdmin(PublishedBaseAdmin):
    '''Base admin class for OnlineModelBase instances.'''

    actions = ('publish_selected', 'unpublish_selected',)

    list_display = ('__str__', 'is_online',)

    list_filter = ('is_online',)

    PUBLICATION_FIELDS = (_('Publication'), {
        'fields': ('is_online',),
        'classes': ('collapse',),
    })

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj=obj, change=change, **kwargs)
        form.base_fields['is_online'].initial = defaults.ONLINE_DEFAULT
        return form

    # Custom admin actions.
    def publish_selected(self, request, queryset):
        '''Publishes the selected models.'''
        queryset.update(is_online=True)
    publish_selected.short_description = 'Place selected %(verbose_name_plural)s online'

    def unpublish_selected(self, request, queryset):
        '''Unpublishes the selected models.'''
        queryset.update(is_online=False)
    unpublish_selected.short_description = 'Take selected %(verbose_name_plural)s offline'


class SearchMetaBaseAdmin(OnlineBaseAdmin, VersionAdmin, SearchAdmin):
    '''Base admin class for SearchMetaBase models.'''

    adapter_cls = SearchMetaBaseSearchAdapter

    list_display = ('__str__', 'is_online',)

    list_filter = OnlineBaseAdmin.list_filter + (SEOQualityControlFilter,)

    SEO_FIELDS = (_('SEO'), {
        'fields': ('browser_title', 'meta_description', 'sitemap_priority', 'sitemap_changefreq', 'robots_index', 'robots_follow', 'robots_archive',),
        'classes': ('collapse',),
    })

    OPENGRAPH_FIELDS = (_('Open Graph'), {
        'fields': ('og_title', 'og_description', 'og_image'),
        'classes': ('collapse',)
    })

    OPENGRAPH_TWITTER_FIELDS = (_('Twitter card'), {
        'fields': ('twitter_card', 'twitter_title', 'twitter_description', 'twitter_image'),
        'classes': ('collapse',)
    })


class PageBaseAdmin(SearchMetaBaseAdmin):
    '''Base admin class for PageBase models.'''

    prepopulated_fields = {'slug': ('title',), }

    search_fields = ('title', 'meta_description',)

    adapter_cls = PageBaseSearchAdapter

    TITLE_FIELDS = (None, {
        'fields': ('title', 'slug',),
    })

    fieldsets = [
        TITLE_FIELDS,
        OnlineBaseAdmin.PUBLICATION_FIELDS,
        SearchMetaBaseAdmin.SEO_FIELDS,
        SearchMetaBaseAdmin.OPENGRAPH_FIELDS,
        SearchMetaBaseAdmin.OPENGRAPH_TWITTER_FIELDS
    ]

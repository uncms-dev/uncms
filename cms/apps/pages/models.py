'''Core models used by the CMS.'''
from django import urls
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db import connection, models, transaction
from django.db.models import F, Q
from django.utils import timezone
from django.utils.encoding import force_text
from django.utils.functional import cached_property
from historylinks import shortcuts as historylinks
from reversion.models import Version

from cms import sitemaps
from cms.models import OnlineBaseManager, PageBase, PageBaseSearchAdapter
from cms.models.managers import publication_manager


class PageManager(OnlineBaseManager):

    '''Manager for Page objects.'''

    def select_published(self, queryset, page_alias=None):  # pylint:disable=arguments-differ
        '''Selects only published pages.'''
        queryset = super().select_published(queryset)
        now = timezone.now().replace(second=0, microsecond=0)
        # Perform local filtering.
        queryset = queryset.filter(
            Q(publication_date=None) | Q(publication_date__lte=now))
        queryset = queryset.filter(Q(expiry_date=None) | Q(expiry_date__gt=now))
        # Perform parent ordering.
        quote_name = connection.ops.quote_name
        page_alias = page_alias or quote_name('pages_page')
        queryset = queryset.extra(
            where=('''
                NOT EXISTS (
                    SELECT *
                    FROM {pages_page} AS {ancestors}
                    WHERE
                        {ancestors}.{left} < {page_alias}.{left} AND
                        {ancestors}.{right} > {page_alias}.{right} AND (
                            {ancestors}.{is_online} = FALSE OR
                            {ancestors}.{publication_date} > %s OR
                            {ancestors}.{expiry_date} <= %s
                        )
                )
            '''.format(
                page_alias=page_alias,
                **dict(
                    (name, quote_name(name))
                    for name in (
                        'pages_page',
                        'ancestors',
                        'left',
                        'right',
                        'is_online',
                        'publication_date',
                        'expiry_date',
                    )
                )
            ),),
            params=(now, now),
        )
        return queryset

    def get_homepage(self):
        '''Returns the site homepage.'''
        return self.get(parent=None)


class Page(PageBase):

    '''A page within the site.'''

    objects = PageManager()

    # Hierarchy fields.

    parent = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        related_name='child_set',
        on_delete=models.CASCADE,
    )

    left = models.IntegerField(
        editable=False,
        db_index=True,
    )

    right = models.IntegerField(
        editable=False,
        db_index=True,
    )

    # Publication fields.

    publication_date = models.DateTimeField(
        blank=True,
        null=True,
        db_index=True,
        help_text='The date that this page will appear on the website.  Leave '
                  'this blank to immediately publish this page.',
    )

    expiry_date = models.DateTimeField(
        blank=True,
        null=True,
        db_index=True,
        help_text='The date that this page will be removed from the website.  '
                  'Leave this blank to never expire this page.',
    )

    # Navigation fields.

    in_navigation = models.BooleanField(
        'add to navigation',
        default=True,
        help_text='Uncheck this box to remove this content from the site '
                  'navigation.',
    )

    # Content fields.

    content_type = models.ForeignKey(
        ContentType,
        editable=False,
        help_text='The type of page content.',
        on_delete=models.CASCADE,
    )

    requires_authentication = models.BooleanField(
        default=False,
        help_text='Visitors will need to be logged in to see this page'
    )

    hide_from_anonymous = models.BooleanField(
        'show to logged in only',
        default=False,
        help_text="Visitors that aren't logged in won't see this page in the navigation"
    )

    def __init__(self, *args, **kwargs):
        self.cached_parent = None
        super().__init__(*args, **kwargs)

    def auth_required(self):
        if self.requires_authentication or not self.parent:
            return self.requires_authentication
        return self.parent.auth_required()

    @cached_property
    def children(self):
        '''The child pages for this page.'''
        children = []
        # Optimization - don't fetch children we know aren't there!
        if self.right - self.left > 1:
            for child in self.child_set.all():
                # get_absolute_url will check this first before causing an
                # extra database query looking up its parent page. (It is
                # potentially dangerous to overwrite 'parent'.)
                child.cached_parent = self
                children.append(child)
        return children

    @cached_property
    def content(self):
        '''The associated content model for this page.'''
        content_cls = ContentType.objects.get_for_id(
            self.content_type_id).model_class()
        content = content_cls._default_manager.get(page=self)
        content.page = self
        return content

    @cached_property
    def navigation(self):
        '''The sub-navigation of this page.'''
        return [child for child in self.children if child.in_navigation]

    def reverse(self, view_func, args=None, kwargs=None):
        '''Performs a reverse URL lookup.'''
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}
        urlconf = ContentType.objects.get_for_id(
            self.content_type_id
        ).model_class().urlconf

        return self.get_absolute_url().rstrip('/') + urls.reverse(
            view_func,
            args=args,
            kwargs=kwargs,
            urlconf=urlconf,
        )

    def get_absolute_url(self):
        '''Generates the absolute url of the page.'''
        parent = self.cached_parent or self.parent

        if not parent:
            return urls.get_script_prefix()

        return parent.get_absolute_url() + self.slug + '/'

    # Tree management.

    @property
    def _branch_width(self):
        return self.right - self.left + 1

    def _excise_branch(self):
        '''Excises this whole branch from the tree.'''
        branch_width = self._branch_width
        Page.objects.filter(left__gte=self.left).update(
            left=F('left') - branch_width,
        )
        Page.objects.filter(right__gte=self.left).update(
            right=F('right') - branch_width,
        )

    def _insert_branch(self):
        '''Inserts this whole branch into the tree.'''
        branch_width = self._branch_width
        Page.objects.filter(left__gte=self.left).update(
            left=F('left') + branch_width,
        )
        Page.objects.filter(right__gte=self.left).update(
            right=F('right') + branch_width,
        )

    @transaction.atomic
    def save(self, *args, **kwargs):  # pylint:disable=arguments-differ
        '''Saves the page.'''

        with connection.cursor() as cursor:
            cursor.execute('LOCK TABLE {} IN ROW SHARE MODE'.format(Page._meta.db_table))

            # Lock entire table.
            existing_pages = dict(
                (page['id'], page)
                for page
                in Page.objects.select_for_update().values(
                    'id',
                    'parent_id',
                    'left',
                    'right'
                )
            )

            if self.left is None or self.right is None:
                # This page is being inserted.
                if existing_pages:
                    if not self.parent_id:  # pylint:disable=access-member-before-definition
                        # There is no parent - we're updating the homepage.
                        # Set the parent to be the homepage by default
                        self.parent_id = Page.objects.get_homepage().pk  # pylint:disable=attribute-defined-outside-init

                    parent_right = existing_pages[self.parent_id]['right']
                    # Set the model left and right.
                    self.left = parent_right
                    self.right = self.left + 1
                    # Update the whole tree structure.
                    self._insert_branch()
                else:
                    # This is the first page to be created, ever!
                    self.left = 1
                    self.right = 2
            else:
                # This is an update.
                if self.id not in existing_pages:
                    old_parent_id = -1
                else:
                    old_parent_id = existing_pages[self.id]['parent_id']

                if old_parent_id != self.parent_id:
                    # The page has moved.
                    branch_width = self.right - self.left + 1
                    # Disconnect child branch.
                    if branch_width > 2:
                        Page.objects.filter(
                            left__gt=self.left,
                            right__lt=self.right
                        ).update(
                            left=F('left') * -1,
                            right=F('right') * -1,
                        )
                    self._excise_branch()
                    # Store old left and right values.
                    old_left = self.left
                    old_right = self.right
                    # Put self into the tree.
                    if self.parent_id:
                        parent_right = existing_pages[self.parent_id]['right']
                        if parent_right > self.right:
                            parent_right -= self._branch_width
                        self.left = parent_right
                        self.right = self.left + branch_width - 1
                        self._insert_branch()

                        # Put all children back into the tree.
                        if branch_width > 2:
                            child_offset = self.left - old_left
                            Page.objects.filter(
                                left__lt=-old_left,
                                right__gt=-old_right
                            ).update(
                                left=(F('left') - child_offset) * -1,
                                right=(F('right') - child_offset) * -1,
                            )

        # Now actually save it!
        super().save(*args, **kwargs)

    @transaction.atomic
    def delete(self, *args, **kwargs):  # pylint:disable=arguments-differ
        '''Deletes the page.'''
        list(Page.objects.all().select_for_update().values_list(
            'left',
            'right'
        ))  #
        # Lock entire
        #  table.
        super().delete(*args, **kwargs)
        # Update the entire tree.
        self._excise_branch()

    def last_modified(self):
        versions = Version.objects.get_for_object(self)
        if versions.count() > 0:
            latest_version = versions[:1][0]
            return '{} by {}'.format(
                latest_version.revision.date_created.strftime('%Y-%m-%d %H:%M:%S'),
                latest_version.revision.user
            )
        return '-'

    class Meta:
        unique_together = (('parent', 'slug'),)
        ordering = ('left',)


historylinks.register(Page)


class PageSitemap(sitemaps.PageBaseSitemap):

    '''Sitemap for page models.'''

    model = Page

    def items(self):
        '''Only lists items that are marked as indexable.'''
        return filter_indexable_pages(super().items())


sitemaps.register(Page, sitemap_cls=PageSitemap)


class PageSearchAdapter(PageBaseSearchAdapter):

    '''Search adapter for Page models.'''

    def get_content(self, obj):
        '''Returns the search text for the page.'''
        content_obj = obj.content

        return ' '.join([
            super().get_content(obj),
            self.prepare_content(content_obj.get_searchable_text())
        ])

    def get_live_queryset(self):
        '''Selects the live page queryset.'''
        # HACK: Prevents a table name collision in the Django queryset manager.
        with publication_manager.select_published(False):
            qs = Page._base_manager.all()
        if publication_manager.select_published_active():
            qs = Page.objects.select_published(qs, page_alias='U0')
        # Filter out unindexable pages.
        qs = filter_indexable_pages(qs)
        # All done!
        return qs


# Base content class.

def get_registered_content():
    '''Returns a list of all registered content objects.'''
    return [
        model for model in apps.get_models()
        if issubclass(model, ContentBase) and not model._meta.abstract
    ]


def filter_indexable_pages(queryset):
    '''
    Filters the given queryset of pages to only contain ones that should be
    indexed by search engines.
    '''
    return queryset.filter(
        robots_index=True,
        content_type__in=[
            ContentType.objects.get_for_model(content_model)
            for content_model
            in get_registered_content()
            if content_model.robots_index
        ]
    )


class ContentBase(models.Model):

    '''Base class for page content.'''

    # This must be a 64 x 64 pixel image.
    icon = 'pages/img/content.png'

    # The heading that the admin places this content under.
    classifier = 'content'

    # The urlconf used to power this content's views.
    urlconf = 'cms.apps.pages.urls'

    # A fieldset definition. If blank, one will be generated.
    fieldsets = None

    # Whether pages of this type should be included in search indexes. (Can
    # still be disabled on a per-page basis).
    robots_index = True

    page = models.OneToOneField(
        Page,
        primary_key=True,
        editable=False,
        related_name='+',
        on_delete=models.CASCADE,
    )

    def __str__(self):
        '''Returns a unicode representation.'''
        return self.page.title

    class Meta:
        abstract = True

    def get_searchable_text(self):
        '''
        Returns a blob of text that will be indexed by Watson. This will be
        given lower priority than the title of the page it is attached to.

        By default this will return every text field on the ContentBase,
        separated by a space. A common case for overriding this is when your
        page's content is built out of other models.
        '''
        return ' '.join([
            force_text(getattr(self, field_name))
            for field_name in [
                field.name for field
                in self._meta.fields
                if isinstance(field, (models.CharField, models.TextField))
            ]
            # Because we don't want to index "None" :)
            if getattr(self, field_name)
        ])

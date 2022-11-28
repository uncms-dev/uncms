'''Tests for the pages app.'''
from datetime import timedelta

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.test import TestCase
from django.utils.timezone import now
from reversion import create_revision
from watson import search

from tests.pages.factories import PageFactory
from tests.testing_app.models import (
    EmptyTestPage,
    PageContent,
    PageContentWithSections,
)
from uncms.apps.pages.models import (
    Page,
    PageSearchAdapter,
    PageSitemap,
    filter_indexable_pages,
)
from uncms.models.managers import publication_manager


class TestPage(TestCase):

    def setUp(self):
        call_command('installwatson')

        with search.update_index():
            content_type = ContentType.objects.get_for_model(PageContent)

            self.homepage = Page.objects.create(
                title='Homepage',
                slug='homepage',
                content_type=content_type,
            )

            PageContent.objects.create(
                page=self.homepage,
            )

            self.section = Page.objects.create(
                parent=self.homepage,
                title='Section',
                content_type=content_type,
            )

            PageContent.objects.create(
                page=self.section,
            )

            self.subsection = Page.objects.create(
                parent=self.section,
                title='Subsection',
                content_type=content_type,
            )

            PageContent.objects.create(
                page=self.subsection,
            )

            self.subsubsection = Page.objects.create(
                parent=self.subsection,
                title='Subsubsection',
                content_type=content_type,
            )

            PageContent.objects.create(
                page=self.subsubsection,
            )

    def test_children(self):
        homepage = Page.objects.get_homepage()
        subsection = homepage.children[0].children[0]
        self.assertEqual(subsection.title, 'Subsection')
        subsection = homepage.navigation[0].navigation[0]
        self.assertEqual(subsection.title, 'Subsection')
        subsubsection = subsection.children[0]
        self.assertEqual(subsubsection.title, 'Subsubsection')
        subsubsection = subsection.children[0]
        self.assertEqual(subsubsection.title, 'Subsubsection')

    def test_filter_indexable_pages(self):
        pages = Page.objects.all()
        self.assertEqual(len(pages), 4)

        pages = filter_indexable_pages(Page.objects.all())
        self.assertEqual(len(pages), 4)

        # Turn off indexing on the homepage.
        self.homepage.robots_index = False
        self.homepage.save()

        pages = filter_indexable_pages(Page.objects.all())
        self.assertEqual(len(pages), 3)

    def test_pagesitemap_items(self):
        sitemap = PageSitemap()
        self.assertEqual(len(sitemap.items()), 4)

        # Turn off indexing on the homepage.
        self.homepage.robots_index = False
        self.homepage.save()

        self.assertEqual(len(sitemap.items()), 3)


class TestPageComplex(TestCase):

    '''
    Page structure:

                                  Homepage
                                     |
                  +------------------+-----------------------+
                  |                  |                       |
           Tree 1 - Page 1    Tree 2 - Page 1         Tree 3 - Page 1
                  |                                          |
       +----------+----------+                    +----------+----------+
       |                     |                    |                     |
 Tree 1 - Page 2      Tree 1 - Page 3      Tree 3 - Page 2       Tree 3 - Page 3
                                                  |
                                       +----------+----------+
                                       |                     |
                                Tree 3 - Page 4       Tree 3 - Page 5

    '''

    def setUp(self):
        structure = {
            'title': 'Homepage',
            'children': [
                {
                    'title': 'Tree 1 - Page 1',
                    'children': [
                        {
                            'title': 'Tree 1 - Page 2'
                        },
                        {
                            'title': 'Tree 1 - Page 3'
                        }
                    ]
                },
                {
                    'title': 'Tree 2 - Page 1'
                },
                {
                    'title': 'Tree 3 - Page 1',
                    'children': [
                        {
                            'title': 'Tree 3 - Page 2',
                            'children': [
                                {
                                    'title': 'Tree 3 - Page 4'
                                },
                                {
                                    'title': 'Tree 3 - Page 5'
                                }
                            ]
                        },
                        {
                            'title': 'Tree 3 - Page 3'
                        }
                    ]
                }
            ]
        }

        content_type = ContentType.objects.get_for_model(PageContent)
        self.page_ids = {}
        self.pages = {}

        def _add_page(page, parent=None):
            slug = page['title'].replace(' ', '_').replace('-', '_')

            page_obj = Page.objects.create(
                title=page['title'],
                slug=slug,
                content_type=content_type,
                parent=parent,
            )

            PageContent.objects.create(
                page=page_obj,
            )

            self.page_ids[slug] = page_obj.pk

            if page.get('children', None):
                for child in page['children']:
                    _add_page(child, page_obj)

        with search.update_index():
            _add_page(structure)
            self._rebuild_page_dict()

    def _rebuild_page_dict(self):
        self.pages = {}
        for key, value in self.page_ids.items():
            try:
                self.pages[key] = Page.objects.get(pk=value)
            # Handle tests involving deletions.
            except Page.DoesNotExist:
                pass

    def test_page_excise_branch(self):
        # Excising a branch which hasn't been deleted should have no affect.
        self.assertEqual(self.pages['Homepage'].left, 1)
        self.assertEqual(self.pages['Homepage'].right, 20)
        self.assertEqual(self.pages['Tree_1___Page_1'].left, 2)
        self.assertEqual(self.pages['Tree_1___Page_1'].right, 7)
        self.assertEqual(self.pages['Tree_1___Page_2'].left, 3)
        self.assertEqual(self.pages['Tree_1___Page_2'].right, 4)
        self.assertEqual(self.pages['Tree_1___Page_3'].left, 5)
        self.assertEqual(self.pages['Tree_1___Page_3'].right, 6)
        self.assertEqual(self.pages['Tree_2___Page_1'].left, 8)
        self.assertEqual(self.pages['Tree_2___Page_1'].right, 9)
        self.assertEqual(self.pages['Tree_3___Page_1'].left, 10)
        self.assertEqual(self.pages['Tree_3___Page_1'].right, 19)
        self.assertEqual(self.pages['Tree_3___Page_2'].left, 11)
        self.assertEqual(self.pages['Tree_3___Page_2'].right, 16)
        self.assertEqual(self.pages['Tree_3___Page_3'].left, 17)
        self.assertEqual(self.pages['Tree_3___Page_3'].right, 18)
        self.assertEqual(self.pages['Tree_3___Page_4'].left, 12)
        self.assertEqual(self.pages['Tree_3___Page_4'].right, 13)
        self.assertEqual(self.pages['Tree_3___Page_5'].left, 14)
        self.assertEqual(self.pages['Tree_3___Page_5'].right, 15)

        self.pages['Homepage']._excise_branch()

        self.assertEqual(self.pages['Homepage'].left, 1)
        self.assertEqual(self.pages['Homepage'].right, 20)
        self.assertEqual(self.pages['Tree_1___Page_1'].left, 2)
        self.assertEqual(self.pages['Tree_1___Page_1'].right, 7)
        self.assertEqual(self.pages['Tree_1___Page_2'].left, 3)
        self.assertEqual(self.pages['Tree_1___Page_2'].right, 4)
        self.assertEqual(self.pages['Tree_1___Page_3'].left, 5)
        self.assertEqual(self.pages['Tree_1___Page_3'].right, 6)
        self.assertEqual(self.pages['Tree_2___Page_1'].left, 8)
        self.assertEqual(self.pages['Tree_2___Page_1'].right, 9)
        self.assertEqual(self.pages['Tree_3___Page_1'].left, 10)
        self.assertEqual(self.pages['Tree_3___Page_1'].right, 19)
        self.assertEqual(self.pages['Tree_3___Page_2'].left, 11)
        self.assertEqual(self.pages['Tree_3___Page_2'].right, 16)
        self.assertEqual(self.pages['Tree_3___Page_3'].left, 17)
        self.assertEqual(self.pages['Tree_3___Page_3'].right, 18)
        self.assertEqual(self.pages['Tree_3___Page_4'].left, 12)
        self.assertEqual(self.pages['Tree_3___Page_4'].right, 13)
        self.assertEqual(self.pages['Tree_3___Page_5'].left, 14)
        self.assertEqual(self.pages['Tree_3___Page_5'].right, 15)

    def test_page_save__create_with_sides(self):
        with search.update_index():
            content_type = ContentType.objects.get_for_model(PageContent)

            # Create a page with a manual left and right defined.
            page_obj = Page.objects.create(
                title='Foo',
                content_type=content_type,
                parent=self.pages['Tree_1___Page_1'],
                left=7,
                right=8,
            )

            PageContent.objects.create(
                page=page_obj,
            )

            self.assertEqual(page_obj.title, 'Foo')

    def test_page_save__move_branch_left(self):
        self.assertEqual(self.pages['Homepage'].left, 1)
        self.assertEqual(self.pages['Homepage'].right, 20)
        self.assertEqual(self.pages['Tree_1___Page_1'].left, 2)
        self.assertEqual(self.pages['Tree_1___Page_1'].right, 7)
        self.assertEqual(self.pages['Tree_1___Page_2'].left, 3)
        self.assertEqual(self.pages['Tree_1___Page_2'].right, 4)
        self.assertEqual(self.pages['Tree_1___Page_3'].left, 5)
        self.assertEqual(self.pages['Tree_1___Page_3'].right, 6)
        self.assertEqual(self.pages['Tree_2___Page_1'].left, 8)
        self.assertEqual(self.pages['Tree_2___Page_1'].right, 9)
        self.assertEqual(self.pages['Tree_3___Page_1'].left, 10)
        self.assertEqual(self.pages['Tree_3___Page_1'].right, 19)
        self.assertEqual(self.pages['Tree_3___Page_2'].left, 11)
        self.assertEqual(self.pages['Tree_3___Page_2'].right, 16)
        self.assertEqual(self.pages['Tree_3___Page_3'].left, 17)
        self.assertEqual(self.pages['Tree_3___Page_3'].right, 18)
        self.assertEqual(self.pages['Tree_3___Page_4'].left, 12)
        self.assertEqual(self.pages['Tree_3___Page_4'].right, 13)
        self.assertEqual(self.pages['Tree_3___Page_5'].left, 14)
        self.assertEqual(self.pages['Tree_3___Page_5'].right, 15)

        self.pages['Tree_3___Page_1'].parent = self.pages['Tree_1___Page_1']
        self.pages['Tree_3___Page_1'].save()

        # Rebuild page dict.
        self._rebuild_page_dict()

        self.assertEqual(self.pages['Homepage'].left, 1)
        self.assertEqual(self.pages['Homepage'].right, 20)
        self.assertEqual(self.pages['Tree_1___Page_1'].left, 2)
        self.assertEqual(self.pages['Tree_1___Page_1'].right, 17)
        self.assertEqual(self.pages['Tree_1___Page_2'].left, 3)
        self.assertEqual(self.pages['Tree_1___Page_2'].right, 4)
        self.assertEqual(self.pages['Tree_1___Page_3'].left, 5)
        self.assertEqual(self.pages['Tree_1___Page_3'].right, 6)
        self.assertEqual(self.pages['Tree_2___Page_1'].left, 18)
        self.assertEqual(self.pages['Tree_2___Page_1'].right, 19)
        self.assertEqual(self.pages['Tree_3___Page_1'].left, 7)
        self.assertEqual(self.pages['Tree_3___Page_1'].right, 16)
        self.assertEqual(self.pages['Tree_3___Page_2'].left, 8)
        self.assertEqual(self.pages['Tree_3___Page_2'].right, 13)
        self.assertEqual(self.pages['Tree_3___Page_3'].left, 14)
        self.assertEqual(self.pages['Tree_3___Page_3'].right, 15)
        self.assertEqual(self.pages['Tree_3___Page_4'].left, 9)
        self.assertEqual(self.pages['Tree_3___Page_4'].right, 10)
        self.assertEqual(self.pages['Tree_3___Page_5'].left, 11)
        self.assertEqual(self.pages['Tree_3___Page_5'].right, 12)

    def test_page_save__move_branch_right(self):
        self.assertEqual(self.pages['Homepage'].left, 1)
        self.assertEqual(self.pages['Homepage'].right, 20)
        self.assertEqual(self.pages['Tree_1___Page_1'].left, 2)
        self.assertEqual(self.pages['Tree_1___Page_1'].right, 7)
        self.assertEqual(self.pages['Tree_1___Page_2'].left, 3)
        self.assertEqual(self.pages['Tree_1___Page_2'].right, 4)
        self.assertEqual(self.pages['Tree_1___Page_3'].left, 5)
        self.assertEqual(self.pages['Tree_1___Page_3'].right, 6)
        self.assertEqual(self.pages['Tree_2___Page_1'].left, 8)
        self.assertEqual(self.pages['Tree_2___Page_1'].right, 9)
        self.assertEqual(self.pages['Tree_3___Page_1'].left, 10)
        self.assertEqual(self.pages['Tree_3___Page_1'].right, 19)
        self.assertEqual(self.pages['Tree_3___Page_2'].left, 11)
        self.assertEqual(self.pages['Tree_3___Page_2'].right, 16)
        self.assertEqual(self.pages['Tree_3___Page_3'].left, 17)
        self.assertEqual(self.pages['Tree_3___Page_3'].right, 18)
        self.assertEqual(self.pages['Tree_3___Page_4'].left, 12)
        self.assertEqual(self.pages['Tree_3___Page_4'].right, 13)
        self.assertEqual(self.pages['Tree_3___Page_5'].left, 14)
        self.assertEqual(self.pages['Tree_3___Page_5'].right, 15)

        self.pages['Tree_1___Page_1'].parent = self.pages['Tree_3___Page_1']
        self.pages['Tree_1___Page_1'].save()

        # Rebuild page dict.
        self._rebuild_page_dict()

        self.assertEqual(self.pages['Homepage'].left, 1)
        self.assertEqual(self.pages['Homepage'].right, 20)
        self.assertEqual(self.pages['Tree_1___Page_1'].left, 13)
        self.assertEqual(self.pages['Tree_1___Page_1'].right, 18)
        self.assertEqual(self.pages['Tree_1___Page_2'].left, 14)
        self.assertEqual(self.pages['Tree_1___Page_2'].right, 15)
        self.assertEqual(self.pages['Tree_1___Page_3'].left, 16)
        self.assertEqual(self.pages['Tree_1___Page_3'].right, 17)
        self.assertEqual(self.pages['Tree_2___Page_1'].left, 2)
        self.assertEqual(self.pages['Tree_2___Page_1'].right, 3)
        self.assertEqual(self.pages['Tree_3___Page_1'].left, 4)
        self.assertEqual(self.pages['Tree_3___Page_1'].right, 19)
        self.assertEqual(self.pages['Tree_3___Page_2'].left, 5)
        self.assertEqual(self.pages['Tree_3___Page_2'].right, 10)
        self.assertEqual(self.pages['Tree_3___Page_3'].left, 11)
        self.assertEqual(self.pages['Tree_3___Page_3'].right, 12)
        self.assertEqual(self.pages['Tree_3___Page_4'].left, 6)
        self.assertEqual(self.pages['Tree_3___Page_4'].right, 7)
        self.assertEqual(self.pages['Tree_3___Page_5'].left, 8)
        self.assertEqual(self.pages['Tree_3___Page_5'].right, 9)

    def test_page_delete(self):
        self.pages['Tree_3___Page_5'].content.delete()
        self.pages['Tree_3___Page_5'].delete()

        # Rebuild page dict.
        self._rebuild_page_dict()

        self.assertEqual(self.pages['Homepage'].left, 1)
        self.assertEqual(self.pages['Homepage'].right, 18)
        self.assertEqual(self.pages['Tree_1___Page_1'].left, 2)
        self.assertEqual(self.pages['Tree_1___Page_1'].right, 7)
        self.assertEqual(self.pages['Tree_1___Page_2'].left, 3)
        self.assertEqual(self.pages['Tree_1___Page_2'].right, 4)
        self.assertEqual(self.pages['Tree_1___Page_3'].left, 5)
        self.assertEqual(self.pages['Tree_1___Page_3'].right, 6)
        self.assertEqual(self.pages['Tree_2___Page_1'].left, 8)
        self.assertEqual(self.pages['Tree_2___Page_1'].right, 9)
        self.assertEqual(self.pages['Tree_3___Page_1'].left, 10)
        self.assertEqual(self.pages['Tree_3___Page_1'].right, 17)
        self.assertEqual(self.pages['Tree_3___Page_2'].left, 11)
        self.assertEqual(self.pages['Tree_3___Page_2'].right, 14)
        self.assertEqual(self.pages['Tree_3___Page_3'].left, 15)
        self.assertEqual(self.pages['Tree_3___Page_3'].right, 16)
        self.assertEqual(self.pages['Tree_3___Page_4'].left, 12)
        self.assertEqual(self.pages['Tree_3___Page_4'].right, 13)

        with self.assertRaises(KeyError):
            self.pages['Tree_3___Page_5']  # pylint:disable=pointless-statement


@pytest.mark.django_db
def test_contentbase_str():
    page = PageFactory(title='Awesome')
    assert str(page.content) == 'Awesome'


@pytest.mark.django_db
def test_page_content(django_assert_num_queries):
    """
    Guard against performance regression on Page.content.
    """
    page = PageFactory()
    # content has been created from the factory, so reload...
    page = Page.objects.get(pk=page.pk)

    with django_assert_num_queries(1):
        assert isinstance(page.content, EmptyTestPage)

    with django_assert_num_queries(0):
        assert isinstance(page.content, EmptyTestPage)


@pytest.mark.django_db
def test_page_last_modified():
    page = PageFactory()
    # We have no versions
    assert page.last_modified() == '-'

    # Create an initial revision.
    with create_revision():
        page.save()

    # We have reversion and a version in the db, last_modified should not be empty
    assert page.last_modified() != '-'


@pytest.mark.django_db
def test_page_publication_date():
    for _ in range(4):
        PageFactory.create(publication_date=now() + timedelta(days=10))

    with publication_manager.select_published(True):
        assert Page.objects.count() == 0

    with publication_manager.select_published(False):
        assert Page.objects.count() == 4

    # We need to generate an exception within the published block.
    with pytest.raises(TypeError), publication_manager.select_published(True):
        assert 1 / 'a'


@pytest.mark.django_db
def test_page_reverse():
    page = PageFactory(content=PageContent())

    url = page.reverse('index')
    assert url == '/'

    url = page.reverse('detail', kwargs={
        'slug': 'sample',
    })
    assert url == '/sample/'

    subpage = PageFactory(slug='subpage', content=PageContent(), parent=page)

    url = subpage.reverse('index')
    assert url == '/subpage/'

    url = subpage.reverse('detail', kwargs={
        'slug': 'sample',
    })
    assert url == '/subpage/sample/'


@pytest.mark.django_db
def test_page_str():
    page = PageFactory(
        title='Home page',
        short_title='Home',
    )
    assert page.slug == 'home-page'
    assert str(page) == 'Home'
    page.short_title = None
    assert str(page) == 'Home page'


@pytest.mark.django_db
def test_pagesearchadapter_get_live_queryset():
    call_command('installwatson')

    def do_search():
        return search.search('Sparkles', models=(Page,))

    page = PageFactory(title='Sparkles')
    assert len(do_search()) == 1

    with publication_manager.select_published(True):
        assert len(do_search()) == 1

        # Take it offline, save...
        page.is_online = False
        page.save()
        # ...and it should no longer be in the results
        assert len(do_search()) == 0


@pytest.mark.django_db
def test_pagesearchadapter_get_content():
    page = PageFactory(title='Homepage', content=PageContentWithSections())
    search_adapter = PageSearchAdapter(Page)

    content = search_adapter.get_content(page)
    assert content == '      homepage Homepage  testing'


@pytest.mark.django_db
def test_page_get_absolute_url():
    page = PageFactory()
    assert page.get_absolute_url() == '/'

    page2 = PageFactory(parent=page, slug='subpage')
    assert page2.get_absolute_url() == '/subpage/'


@pytest.mark.django_db
def test_page_get_absolute_url_on_children_is_efficient(django_assert_num_queries):
    """
    A previous version of `pages.children` (which got split into two parts
    later, get_children() and cached-property children) used to do an
    "optimisation" of setting the parent page on the child page. I wrote this
    test to prove it was unnecessary, but it doubles as a regression test to
    make sure `get_absolute_url` (which is used on every entry in the
    navigation) does not regress.
    """
    PageFactory.create_tree(1, 1)

    top_level = Page.objects.get(parent=None)

    with django_assert_num_queries(1):
        child = top_level.children[0]

    with django_assert_num_queries(0):
        child.get_absolute_url()


@pytest.mark.django_db
def test_page_get_children_is_efficient(django_assert_num_queries):
    """
    This is a long-standing comment in Page.get_children, dating all the way
    back to 2012:

        # Optimization - don't fetch children we know aren't there!

    The code looks alright, but this test was written to ensure that this is
    really the case. Let's be sure!
    """
    PageFactory.create()
    homepage = Page.objects.get_homepage()

    # The homepage has no children. This should result in zero database
    # queries.
    with django_assert_num_queries(0):
        assert not homepage.get_children()

    for _ in range(2):
        PageFactory.create(parent=homepage)

    # Just to make sure something wasn't really bad earlier, let's make sure
    # that we do in fact cause a query if it does have children.
    homepage = Page.objects.get_homepage()
    with django_assert_num_queries(1):
        assert len(homepage.get_children()) == 2

    # Let's be sure that these child pages do not cause a database query
    # either.
    child = Page.objects.filter(parent=Page.objects.get_homepage()).first()
    with django_assert_num_queries(0):
        assert not child.get_children()


@pytest.mark.django_db
def test_page_children_does_not_invalidate_prefetches(django_assert_num_queries):
    """
    In our previous life as Onespacemedia CMS, there used to be extra filtering
    in `.children` which used to invalidate prefetches on Page. That meant
    that prefetching was a pessimisation, so prefetching got removed here:
    https://github.com/onespacemedia/cms/pull/191

    Fortunately, with the multiregion stuff ripped out in the UnCMS era,
    prefetches are now viable again. Let's make sure we have not regressed on
    that one.
    """
    PageFactory.create_tree(1, 1)

    top_level = Page.objects.prefetch_related('child_set', 'child_set__child_set').get(parent=None)

    with django_assert_num_queries(0):
        top_level.children[0].get_absolute_url()
        top_level.children[0].children[0].get_absolute_url()


@pytest.mark.django_db
def test_pagemanager_get_homepage_prefetching(django_assert_num_queries):
    # Create a tree with 3 top-level entries, 5 second-level pages, and 4
    # third-level ones.
    PageFactory.create_tree(3, 5, 2)

    home = Page.objects.get_homepage(prefetch_depth=2)
    with django_assert_num_queries(0):
        children = home.get_children()

    with django_assert_num_queries(0):
        for child in children:
            child.get_children()

    home = Page.objects.get_homepage()
    with django_assert_num_queries(1):
        children = home.get_children()

    # We should expect 3 queries, one for each of the top-level navigation
    # items.
    with django_assert_num_queries(3):
        for child in children:
            child.get_children()


def test_pagemanager_prefetch_children_args():
    assert Page.objects.prefetch_children_args(depth=0) == []
    assert Page.objects.prefetch_children_args(depth=1) == ['child_set']
    assert Page.objects.prefetch_children_args(depth=2) == ['child_set', 'child_set__child_set']
    assert Page.objects.prefetch_children_args(depth=3) == ['child_set', 'child_set__child_set', 'child_set__child_set__child_set']

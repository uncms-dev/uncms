import inspect

import django.template
import pytest
from django.test import RequestFactory, override_settings

from tests.mocks import MockRequestUser, MockSuperUser, request_with_pages
from tests.testing_app.models import (
    ImageFieldModel,
    PageBaseModel,
    TemplateTagTestPage,
)
from uncms.jinja2_environment.pages import \
    get_breadcrumbs as get_breadcrumbs_jinja2
from uncms.jinja2_environment.pages import render_breadcrumbs
from uncms.pages.middleware import RequestPageManager
from uncms.pages.templatetags._common import (
    _navigation_entries,
    get_breadcrumbs_context,
    get_breadcrumbs_obj,
    get_canonical_url,
    get_meta_description,
    get_meta_robots,
    get_og_image,
    get_og_title,
    get_page_url,
    get_twitter_card,
    get_twitter_description,
    get_twitter_image,
    get_twitter_title,
    render_navigation,
)
from uncms.pages.templatetags.uncms_pages import (
    admin_sitemap_entries,
    breadcrumbs,
    get_breadcrumbs,
    meta_description,
    meta_robots,
    navigation,
    og_image,
    og_title,
    page_url,
    twitter_card,
    twitter_description,
    twitter_image,
    twitter_title,
)
from uncms.testhelpers.factories.media import MinimalGIFFileFactory
from uncms.testhelpers.factories.pages import PageFactory
from uncms.utils import canonicalise_url


@pytest.mark.django_db
@pytest.mark.parametrize('test_function', [render_navigation, navigation])
def test_navigation(test_function):
    PageFactory.create_tree(1, 3)
    request = request_with_pages()
    request.user = MockRequestUser(is_authenticated=True)

    nav = test_function({
        'request': request,
    }, request.pages.current.navigation)

    assert len(nav) > 0


def test_navigation_entries(simple_page_tree):
    request = request_with_pages()
    request.user = MockRequestUser(is_authenticated=True)

    nav = _navigation_entries({'request': request}, request.pages.current.navigation)

    assert nav == [
        {
            'url': '/section/',
            'page': simple_page_tree.section,
            'here': False,
            'current': False,
            'title': 'Section',
            'children': [
                {
                    'url': '/section/subsection/',
                    'page': simple_page_tree.subsection,
                    'here': False,
                    'current': False,
                    'title': 'Subsection',
                    'children': [
                        {
                            'url': '/section/subsection/subsubsection/',
                            'page': simple_page_tree.subsubsection,
                            'here': False,
                            'current': False,
                            'title': 'Subsubsection',
                            'children': []
                        }
                    ]
                }
            ]
        }
    ]

    # Test is_json response.
    nav = _navigation_entries({'request': request}, request.pages.current.navigation, json_safe=True)
    assert nav == [
        {
            'url': '/section/',
            'here': False,
            'current': False,
            'title': 'Section',
            'children': [
                {
                    'url': '/section/subsection/',
                    'here': False,
                    'current': False,
                    'title': 'Subsection',
                    'children': [
                        {
                            'url': '/section/subsection/subsubsection/',
                            'here': False,
                            'current': False,
                            'title': 'Subsubsection',
                            'children': []
                        }
                    ]
                }
            ]
        }
    ]

    # Test with section specified.
    nav = _navigation_entries({
        'request': request,
    }, request.pages.current.navigation, section=simple_page_tree.subsubsection)
    assert nav == [
        {
            'url': '/section/subsection/subsubsection/',
            'page': simple_page_tree.subsubsection,
            'here': False,
            'current': False,
            'title': 'Subsubsection',
            'children': []
        },
        {
            'url': '/section/',
            'page': simple_page_tree.section,
            'here': False,
            'current': False,
            'title': 'Section',
            'children': [
                {
                    'url': '/section/subsection/',
                    'page': simple_page_tree.subsection,
                    'here': False,
                    'current': False,
                    'title': 'Subsection',
                    'children': [
                        {
                            'url': '/section/subsection/subsubsection/',
                            'page': simple_page_tree.subsubsection,
                            'current': False,
                            'here': False,
                            'title': 'Subsubsection',
                            'children': []
                        }
                    ]
                }
            ]
        }
    ]

    # Section page isn't visible to non logged in users
    request.user = MockRequestUser(is_authenticated=False)

    nav = _navigation_entries({'request': request}, request.pages.current.navigation)

    assert nav == []


@pytest.mark.django_db
def test_render_navigation_is_efficient(django_assert_num_queries):
    PageFactory.create_tree(5, 5)
    factory = RequestFactory()

    request = factory.get('/')
    request.pages = RequestPageManager(request)

    with django_assert_num_queries(3):
        render_navigation({'request': request}, request.pages.homepage.navigation)


@pytest.mark.django_db
@override_settings(UNCMS={'PAGE_TREE_PREFETCH_DEPTH': 3})
def test_render_navigation_is_efficient_with_deeper_trees(django_assert_num_queries):
    PageFactory.create_tree(5, 5, 5)
    factory = RequestFactory()

    request = factory.get('/')
    request.pages = RequestPageManager(request)

    with django_assert_num_queries(4):
        render_navigation({'request': request}, request.pages.homepage.navigation)


@pytest.mark.django_db
def test_breadcrumbs_django_and_jinja_render_identically(use_jinja2):
    """
    Ensure that Django and Jinja2 versions of the breadcrumbs templates render
    identically.
    """
    subsubpage = PageFactory(title='Subsubpage', parent=PageFactory(parent=PageFactory()))
    obj = PageBaseModel.objects.create(title='Object')

    context = {
        'request': request_with_pages(subsubpage.get_absolute_url()),
        'object': obj,
    }

    jinja_rendered = render_breadcrumbs(context)
    django_rendered = django.template.Template(
        '{% load uncms_pages %}{% breadcrumbs %}',
    ).render(django.template.Context(context))

    assert jinja_rendered.strip() == django_rendered.strip()

    jinja_rendered = render_breadcrumbs(context)
    django_rendered = django.template.Template(
        '{% load uncms_pages %}{% breadcrumbs %}',
    ).render(django.template.Context(context))


@pytest.mark.parametrize('django_function, jinja2_function', [
    (get_breadcrumbs, get_breadcrumbs_jinja2),
    (render_breadcrumbs, breadcrumbs),
])
def test_django_and_jinja_function_parity(django_function, jinja2_function):
    assert inspect.signature(django_function) == inspect.signature(jinja2_function)


@pytest.mark.parametrize('test_function', [breadcrumbs, get_breadcrumbs_context])
@pytest.mark.django_db
def test_breadcrumbs(test_function):
    subsubpage = PageFactory(title='Subsubpage', parent=PageFactory(parent=PageFactory()))
    context = {'request': request_with_pages(subsubpage.get_absolute_url())}

    returned_context = test_function(context)
    assert len(returned_context['breadcrumbs']) == 2
    assert returned_context['class_prefix'] == 'breadcrumbs'
    assert returned_context['breadcrumbs'][0].url == subsubpage.parent.parent.get_absolute_url()
    assert returned_context['breadcrumbs'][1].url == subsubpage.parent.get_absolute_url()

    returned_context = test_function(context, class_prefix='breadcrumbs-test')
    assert len(returned_context['breadcrumbs']) == 2
    assert returned_context['class_prefix'] == 'breadcrumbs-test'

    returned_context = test_function(context, show_tail=True)
    assert len(returned_context['breadcrumbs']) == 3
    assert returned_context['class_prefix'] == 'breadcrumbs'
    assert returned_context['breadcrumbs'][2].url == subsubpage.get_absolute_url()


@pytest.mark.django_db
@pytest.mark.parametrize('test_function', [get_breadcrumbs_obj, get_breadcrumbs, get_breadcrumbs_jinja2])
def test_get_breadcrumbs_obj(test_function):
    subsubpage = PageFactory(title='Subsubpage', parent=PageFactory(parent=PageFactory()))
    request = request_with_pages(subsubpage.get_absolute_url())

    def assert_page_items(crumbs_obj):
        assert crumbs_obj.items[0].url == request.pages.homepage.get_absolute_url()
        assert crumbs_obj.items[1].url == subsubpage.parent.get_absolute_url()
        assert crumbs_obj.items[2].url == subsubpage.get_absolute_url()
        assert crumbs_obj.items[2].title == subsubpage.title

    context = {'request': request}
    breadcrumbs_obj = test_function(context)
    assert_page_items(breadcrumbs_obj)

    # Make sure auto-extending with "object" from the context works.
    obj = PageBaseModel.objects.create(title='Object')
    context = {'request': request, 'object': obj}
    breadcrumbs_obj = test_function(context)
    assert_page_items(breadcrumbs_obj)
    assert len(breadcrumbs_obj.items) == 4
    assert breadcrumbs_obj.items[3].title == 'Object'

    # Ensure that bypassing auto extend works
    breadcrumbs_obj = test_function(context, auto_extend=False)
    assert_page_items(breadcrumbs_obj)
    assert len(breadcrumbs_obj.items) == 3

    # Ensure that manually adding objects to extend the breadcrumbs works.
    obj_2 = PageBaseModel.objects.create(title='Object 2')
    context = {'request': request, 'object': obj}
    breadcrumbs_obj = test_function(context, auto_extend=False, extend_with=obj_2)
    assert_page_items(breadcrumbs_obj)
    assert len(breadcrumbs_obj.items) == 4
    assert breadcrumbs_obj.items[3].title == 'Object 2'

    # We also want to be able to pass through a list or iterable of objects.
    obj_3 = PageBaseModel.objects.create(title='Object 3')
    context = {'request': request, 'object': obj}
    breadcrumbs_obj = test_function(context, auto_extend=False, extend_with=[obj_2, obj_3])
    assert_page_items(breadcrumbs_obj)
    assert len(breadcrumbs_obj.items) == 5
    assert breadcrumbs_obj.items[3].title == 'Object 2'
    assert breadcrumbs_obj.items[4].title == 'Object 3'

    context = {'request': request, 'object': obj}
    manual_breadcrumbs = [obj, obj_2]
    breadcrumbs_obj = test_function(context, breadcrumb_list=manual_breadcrumbs, auto_extend=False)
    assert len(breadcrumbs_obj.items) == 2
    assert breadcrumbs_obj.items[0].title == 'Object'
    assert breadcrumbs_obj.items[1].title == 'Object 2'


@override_settings(UNCMS={'SITE_DOMAIN': 'canonicalise.example.com'})
def test_get_canonical_url():
    rf = RequestFactory()

    request = rf.get('/')
    assert get_canonical_url({'request': request}) == 'https://canonicalise.example.com/'

    request = rf.get('/air/')
    assert get_canonical_url({'request': request}) == 'https://canonicalise.example.com/air/'

    with override_settings(DEBUG=True):
        assert get_canonical_url({'request': request}) == 'http://canonicalise.example.com/air/'

    with override_settings(PREPEND_WWW=True):
        assert get_canonical_url({'request': request}) == 'https://www.canonicalise.example.com/air/'


@pytest.mark.django_db
def test_admin_sitemap_entries():
    """
    Ensure our sitemap is not completely broken.
    """
    PageFactory.create_tree(5, 4, 3)
    request = RequestFactory().get('/admin/')
    request.user = MockSuperUser()

    context = admin_sitemap_entries({'request': request})
    entries = context['pages']

    assert len(entries[0]['children']) == 5
    assert len(entries[0]['children'][0]['children']) == 4
    assert len(entries[0]['children'][0]['children'][0]['children']) == 3


@pytest.mark.django_db
@pytest.mark.parametrize('meta_robots_func', [get_meta_robots, meta_robots])
def test_meta_robots(meta_robots_func):
    homepage = PageFactory()

    request = request_with_pages()

    assert meta_robots_func({
        'request': request,
    }, True, True, True) == 'INDEX, FOLLOW, ARCHIVE'

    assert meta_robots_func({
        'request': request,
        'robots_index': True,
        'robots_follow': True,
        'robots_archive': True,
    }) == 'INDEX, FOLLOW, ARCHIVE'

    homepage.robots_index = False
    homepage.robots_follow = False
    homepage.robots_archive = False
    homepage.save()

    request = request_with_pages()

    assert meta_robots_func({
        'request': request,
    }) == 'NOINDEX, NOFOLLOW, NOARCHIVE'

    homepage.delete()

    request = request_with_pages()
    assert meta_robots_func({
        'request': request,
    }) == 'INDEX, FOLLOW, ARCHIVE'


@pytest.mark.django_db
@pytest.mark.parametrize('test_function', [get_meta_description, meta_description])
def test_meta_description(test_function):
    context = {'request': request_with_pages()}
    assert test_function(context) == ''

    homepage = PageFactory()
    context['request'] = request_with_pages()
    assert test_function(context) == ''

    homepage.meta_description = 'Page description'
    homepage.save()
    context['request'] = request_with_pages()
    assert test_function(context) == 'Page description'

    context['meta_description'] = 'Context override'
    assert test_function(context) == 'Context override'


@pytest.mark.django_db
@pytest.mark.parametrize('test_function', [get_og_image, og_image])
def test_og_image(test_function):
    # Test getting it from the current object in the context.
    obj = ImageFieldModel(image=MinimalGIFFileFactory())
    # Used to test falling back to a page
    page = PageFactory(og_image=MinimalGIFFileFactory())

    another_image = MinimalGIFFileFactory()

    request = request_with_pages()
    assert test_function({'request': request, 'object': obj, 'og_image': another_image}) == canonicalise_url(another_image.get_absolute_url())
    assert test_function({'request': request, 'object': obj, 'og_image_url': '/wat.jpg'}) == 'https://example.com/wat.jpg'
    assert test_function({'request': request, 'object': obj}) == canonicalise_url(obj.image.get_absolute_url())
    assert test_function({'request': request}) == canonicalise_url(page.og_image.get_absolute_url())

    page.og_image = None
    page.save()

    request = RequestFactory().get('/')
    request.pages = RequestPageManager(request)
    assert test_function({'request': request}) == ''


@pytest.mark.django_db
@pytest.mark.parametrize('test_function', [get_og_title, og_title])
def test_og_title(test_function):
    context = {'request': request_with_pages()}
    assert test_function(context) == ''

    # Ensure it works with a not-SearchMetaBase "object"
    context['object'] = object()
    assert test_function(context) == ''

    # Test with a page
    page = PageFactory(title='Page title')
    context['request'] = request_with_pages()
    assert test_function(context) == 'Page title'

    # Make sure browser title takes preference.
    page.browser_title = 'Page browser title'
    page.save()
    context['request'] = request_with_pages()
    assert test_function(context) == 'Page browser title'

    # Make sure page OG title takes preference
    page.og_title = 'Page OG title'
    page.save()
    context['request'] = request_with_pages()
    assert test_function(context) == 'Page OG title'

    # Ensure the object takes preference.
    pagelike = PageBaseModel.objects.create(title='Pagelike title')
    context['object'] = pagelike
    assert test_function(context) == 'Pagelike title'

    pagelike.og_title = 'Pagelike OG title'
    assert test_function(context) == 'Pagelike OG title'

    context['og_title'] = 'Context override'
    assert test_function(context) == 'Context override'


@pytest.mark.django_db
@pytest.mark.parametrize('test_function', [get_page_url, page_url])
def test_page_url(test_function):
    page = PageFactory(content=TemplateTagTestPage())
    assert test_function(page) == '/'
    assert test_function(page.pk) == '/'
    assert test_function(-1) == '#'
    assert test_function(None) == '#'
    assert test_function(page.pk, 'detail', slug='subpage') == '/subpage/'


@pytest.mark.django_db
@pytest.mark.parametrize('test_function', [get_twitter_card, twitter_card])
def test_twitter_card(test_function):
    # "product" card type
    homepage = PageFactory(twitter_card=3)
    # "gallery" card type
    subpage = PageFactory(parent=homepage, twitter_card=5)

    request = request_with_pages(subpage.get_absolute_url())
    context = {'request': request}
    assert test_function(context) == 'gallery'

    # Test the context override.
    context['twitter_card'] = 1
    assert test_function(context) == 'photo'

    # Test falling back to the homepage.
    request = request_with_pages('/imaginary/')
    context = {'request': request}
    assert test_function(context) == 'product'


@pytest.mark.django_db
@pytest.mark.parametrize('test_function', [get_twitter_description, twitter_description])
def test_twitter_description(test_function):
    # Ensure ultimate fallback is empty string (not None, or exploding because
    # no pages exist)
    context = {'request': request_with_pages()}
    assert test_function(context) == ''

    # Check fallback again, with pages
    page = PageFactory()
    context['request'] = request_with_pages()
    assert test_function(context) == ''

    # Check that it consults the current page's Twitter description
    page.twitter_description = 'Page description'
    page.save()
    context['request'] = request_with_pages()
    assert test_function(context) == 'Page description'

    # Don't explode with an object which doesn't have a twitter_description
    # field.
    context['object'] = object()
    assert test_function(context) == 'Page description'

    # Ensure current object in context takes precedence.
    context['object'] = PageBaseModel(title='Title', twitter_description='Object description')
    assert test_function(context) == 'Object description'

    # Ensure context takes preference.
    context['twitter_description'] = 'Context description'
    assert test_function(context) == 'Context description'


@pytest.mark.django_db
@pytest.mark.parametrize('test_function', [get_twitter_image, twitter_image])
def test_twitter_image(test_function):
    image = MinimalGIFFileFactory()

    context = {'request': request_with_pages()}

    # Ensure empty string is returned in the case of no pages. (Don't throw an
    # exception before we have started making the site!)
    assert test_function(context) == ''

    # Ensure "not in context" and "in context, but empty" behave identically:
    # fall back to OpenGraph.
    context['twitter_image'] = None
    context['og_image'] = image
    assert test_function(context) == canonicalise_url(image.get_absolute_url())
    del context['twitter_image']
    assert test_function(context) == canonicalise_url(image.get_absolute_url())
    del context['og_image']

    # Test fallback to current page.
    page = PageFactory()
    context['request'] = request_with_pages()
    assert test_function(context) == ''

    page.twitter_image = MinimalGIFFileFactory()
    page.save()
    context['request'] = request_with_pages()
    assert test_function(context) == canonicalise_url(page.twitter_image.get_absolute_url())

    # Test that it uses "object"'s' Twitter image.
    obj = PageBaseModel(title='Test', twitter_image=MinimalGIFFileFactory())
    context['object'] = obj
    assert test_function(context) == canonicalise_url(obj.twitter_image.get_absolute_url())

    context['twitter_image'] = image
    assert test_function(context) == canonicalise_url(image.get_absolute_url())


@pytest.mark.django_db
@pytest.mark.parametrize('test_function', [get_twitter_title, twitter_title])
def test_twitter_title(test_function):
    context = {'request': request_with_pages()}
    # Ensure the fallback is empty string, not None
    assert test_function(context) == ''

    # Ensure the same works with a not-SearchMetaBase "object"
    context['object'] = object()
    assert test_function(context) == ''

    # Test with a page
    page = PageFactory(title='Page title')
    context['request'] = request_with_pages()
    assert test_function(context) == 'Page title'

    # Make sure page twitter_title takes preference
    page.twitter_title = 'Page Twitter title'
    page.save()
    context['request'] = request_with_pages()
    assert test_function(context) == 'Page Twitter title'

    # Ensure the object takes preference.
    pagelike = PageBaseModel.objects.create(title='Pagelike title')
    context['object'] = pagelike
    assert test_function(context) == 'Pagelike title'

    pagelike.twitter_title = 'Pagelike Twitter title'
    assert test_function(context) == 'Pagelike Twitter title'

    context['title'] = 'Context title override'
    assert test_function(context) == 'Context title override'

    context['twitter_title'] = 'Context Twitter override'
    assert test_function(context) == 'Context Twitter override'

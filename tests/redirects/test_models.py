import pytest
from django.core.exceptions import ValidationError
from django.test.utils import override_settings

from uncms.redirects.models import Redirect
from uncms.redirects.types import RedirectTypeChoices


@pytest.mark.django_db
def test_redirectmanager_get_queryset():
    Redirect.objects.create(old_path='/sample/', new_path='/example/', regular_expression=False)
    Redirect.objects.create(old_path='/sample/(.*)/', new_path='/example/', regular_expression=True)

    assert Redirect.objects.count() == 1
    assert Redirect.objects.first().regular_expression is False

    with override_settings(UNCMS={'REGEX_REDIRECTS': True}):
        assert Redirect.objects.count() == 2


@pytest.mark.django_db
def test_redirectmanager_get_for_path():
    non_regex = Redirect.objects.create(
        old_path='/sample/',
        new_path='/example/',
        regular_expression=False,
    )
    regex_redirect = Redirect.objects.create(
        old_path='/sample/(.*)/',
        new_path=r'/example/\1/',
        test_path='/sample/sub/',
        regular_expression=True,
    )

    assert Redirect.objects.get_for_path('/sample/') == non_regex
    assert Redirect.objects.get_for_path('/splat/') is None
    assert Redirect.objects.get_for_path(regex_redirect.test_path) is None

    with override_settings(UNCMS={'REGEX_REDIRECTS': True}):
        assert Redirect.objects.get_for_path('/sample/') == non_regex
        assert Redirect.objects.get_for_path(regex_redirect.test_path) == regex_redirect
        assert Redirect.objects.get_for_path('/splat/') is None


def test_redirect_clean():
    base_data = {
        'old_path': '/example/',
        'new_path': '/sample/',
        'test_path': '/wat/',
        'type': '301',
        'regular_expression': False,
    }

    def make_redirect(extras):
        return Redirect(**{**base_data, **extras})

    # Make sure a good redirect does not raise an exception.
    redirect = Redirect(**base_data)
    redirect.clean()

    # Happy case for regular expression redirects.
    redirect = make_redirect({'regular_expression': True})
    redirect.clean()

    # Ensure you can't redirect something to itself.
    redirect = make_redirect({'new_path': '/example/'})
    with pytest.raises(ValidationError) as exc:
        redirect.clean()
    assert 'New path must not be the same as the old one' in str(exc.value)

    # Ensure a test path is required for regex redirects.
    redirect = make_redirect({'regular_expression': True, 'test_path': ''})
    with pytest.raises(ValidationError) as exc:
        redirect.clean()
    assert 'A test path is necessary' in str(exc.value)

    # Test the "bad regex pattern" branch.
    redirect = make_redirect({'regular_expression': True, 'old_path': '/wobble/('})
    with pytest.raises(ValidationError) as exc:
        redirect.clean()
    assert 'There was an error in your regular expression' in str(exc.value)

    # Test the "nonsense in substitution" branch.
    redirect = make_redirect({'regular_expression': True, 'old_path': '/wobble/(.*)/', 'new_path': r'/wobble/\2/'})
    with pytest.raises(ValidationError) as exc:
        redirect.clean()
    assert 'There was an error in your substitution' in str(exc.value)

    # Test error branches of non-regex redirects.
    redirect = make_redirect({'old_path': 'weygth8eyg'})
    with pytest.raises(ValidationError) as exc:
        redirect.clean()
    assert '"From" path must either be a full URL' in str(exc.value)

    # Test handling of query string parts.
    redirect = make_redirect({'old_path': '/cat/?type=calico'})
    with pytest.raises(ValidationError) as exc:
        redirect.clean()
    assert 'redirects can only work on paths, not on query strings' in str(exc.value)

    # Test old path normalisation.
    redirect = make_redirect({'old_path': 'https://wat.example.invalid/hello/'})
    redirect.clean()
    assert redirect.old_path == '/hello/'

    # Test new path normalisation. It should pass through query strings and
    # fragments and anything else that is not n
    redirect = make_redirect({'new_path': 'https://wat.example.invalid/hello/?query=1#fragment'})
    redirect.clean()
    assert redirect.new_path == 'https://wat.example.invalid/hello/?query=1#fragment'

    with override_settings(ALLOWED_HOSTS=['wat.example.invalid']):
        redirect = make_redirect({'new_path': 'https://wat.example.invalid/hello/?query=1#fragment'})
        redirect.clean()
        assert redirect.new_path == '/hello/?query=1#fragment'


def test_redirect_permanent():
    assert Redirect(old_path='/one/', new_path='/two/').permanent is True
    assert Redirect(old_path='/one/', new_path='/two/', type=RedirectTypeChoices.TEMPORARY).permanent is False


def test_response_response_for_path():
    gone = Redirect(old_path='/sample/', new_path='')
    assert gone.response_for_path('/sample/').status_code == 410

    temporary = Redirect(old_path='/sample/', new_path='/example/', type=RedirectTypeChoices.TEMPORARY)
    response = temporary.response_for_path('/sample/')
    assert response.status_code == 302
    assert response['Location'] == '/example/'

    temporary = Redirect(old_path='/sample/', new_path='/example/', type=RedirectTypeChoices.PERMANENT)
    response = temporary.response_for_path('/sample/')
    assert response.status_code == 301
    assert response['Location'] == '/example/'


def test_redirect_str():
    assert str(Redirect(old_path='/stringme/')) == '/stringme/'
    assert str(Redirect(old_path='/stringme/', new_path='/stringme2/')) == '/stringme/ 🡢 /stringme2/'


@pytest.mark.django_db
def test_redirect_sub_path():
    non_regex = Redirect.objects.create(
        old_path='/sample/',
        new_path='/example/',
        regular_expression=False,
    )
    regex_redirect = Redirect.objects.create(
        old_path='/sample/(.*)/',
        new_path=r'/example/\1/',
        test_path='/sample/sub/',
        regular_expression=True,
    )

    assert non_regex.sub_path('/sample/') == '/example/'
    assert regex_redirect.sub_path('/sample/wicked/') == '/example/wicked/'


@pytest.mark.django_db
def test_redirect_type_default():
    # looks silly, but it puts my mind at ease
    assert Redirect.objects.create(old_path='/wobble/', new_path='/wat/').type == '301'

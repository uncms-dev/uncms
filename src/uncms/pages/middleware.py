'''Custom middleware used by the pages application.'''

import sys

from django import urls
from django.conf import settings
from django.core.handlers.exception import handle_uncaught_exception
from django.http import Http404
from django.shortcuts import redirect
from django.template.response import SimpleTemplateResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import cached_property
from django.views.debug import technical_404_response

from uncms.conf import defaults
from uncms.pages import get_page_model


class RequestPageManager:

    '''Handles loading page objects.'''

    def __init__(self, request):
        '''Initializes the RequestPageManager.'''
        self.request = request
        self.path = self.request.path
        self.path_info = self.request.path_info
        self.page_model = get_page_model()

    @cached_property
    def homepage(self):
        '''Returns the site homepage.'''
        try:
            return self.page_model.objects.get_homepage(prefetch_depth=defaults.PAGE_TREE_PREFETCH_DEPTH)
        except self.page_model.DoesNotExist:
            return None

    @cached_property
    def is_homepage(self):
        '''Whether the current request is for the site homepage.'''
        return self.path == self.homepage.get_absolute_url()

    @cached_property
    def breadcrumbs(self):
        '''The breadcrumbs for the current request.'''
        breadcrumbs = []
        slugs = self.path_info.strip('/').split('/')
        slugs.reverse()

        def do_breadcrumbs(page):
            breadcrumbs.append(page)
            if slugs:
                slug = slugs.pop()
                for child in page.children:
                    if child.slug == slug:
                        do_breadcrumbs(child)
                        break
        if self.homepage:
            do_breadcrumbs(self.homepage)
        return breadcrumbs

    @cached_property
    def section(self):
        '''The current primary level section, or None.'''
        try:
            return self.breadcrumbs[1]
        except IndexError:
            return None

    @cached_property
    def subsection(self):
        '''The current secondary level section, or None.'''
        try:
            return self.breadcrumbs[2]
        except IndexError:
            return None

    @cached_property
    def current(self):
        '''The current best-matched page.'''
        try:
            return self.breadcrumbs[-1]
        except IndexError:
            return None

    @cached_property
    def is_exact(self):
        '''Whether the current page exactly matches the request URL.'''
        return self.current.get_absolute_url() == self.path

    def get_page(self, page):
        def find_recursive(children, find_id):
            if not children:
                return None

            for child in children:
                if child.id == find_id:
                    return child
                found = find_recursive(child.children, find_id)
                if found:
                    return found
            return None

        if not self.homepage:
            return None

        if isinstance(page, self.page_model):
            page_id = page.pk
        else:
            page_id = int(page)

        return find_recursive([self.homepage], page_id)


class PageMiddleware(MiddlewareMixin):

    '''Serves up pages when no other view is matched.'''

    def process_request(self, request):
        '''Annotates the request with a page manager.'''
        request.pages = RequestPageManager(request)

    def process_response(self, request, response):  # pylint:disable=too-many-return-statements
        '''If the response was a 404, attempt to serve up a page.'''
        if response.status_code != 404:
            return response

        # Get the current page.
        page = request.pages.current
        if page is None:
            return response
        script_name = page.get_absolute_url()[:-1]
        path_info = request.path[len(script_name):]

        # Continue for media and static files.
        for setting in [settings.MEDIA_URL, settings.STATIC_URL]:
            if setting and request.path.startswith(setting):
                return response

        # Dispatch to the content.
        try:
            try:
                callback, callback_args, callback_kwargs = urls.resolve(path_info, page.content.urlconf)
            except urls.Resolver404:
                # First of all see if adding a slash will help matters.
                if settings.APPEND_SLASH:
                    new_path_info = path_info + '/'

                    try:
                        urls.resolve(new_path_info, page.content.urlconf)
                    except urls.Resolver404:
                        pass
                    else:
                        return redirect(script_name + new_path_info, permanent=True)
                return response

            # Redirect to the login URL if this page requires authentication.
            # We do this after checking the page exists because we don't want
            # to redirect and then 404 after they have logged in. But in case
            # the callback has some side-effect which would not be desirable
            # for logged-out users, we want to do the auth check first.
            if page.auth_required() and not request.user.is_authenticated:
                return redirect('{}?next={}'.format(
                    settings.LOGIN_URL,
                    request.path
                ))

            response = callback(request, *callback_args, **callback_kwargs)
            # Validate the response.
            if not response:
                raise ValueError("The view {0!r} didn't return an HttpResponse object.".format(
                    callback.__name__
                ))

            if isinstance(response, SimpleTemplateResponse):
                return response.render()

            return response
        except Http404 as ex:
            if settings.DEBUG:
                return technical_404_response(request, ex)
            # Let the normal 404 mechanisms render an error page.
            return response
        except:  # pylint:disable=bare-except
            return handle_uncaught_exception(request, urls.get_resolver(None), sys.exc_info())

'''Custom middleware used by the pages application.'''

import re

from django.template.response import SimpleTemplateResponse
from django.utils.deprecation import MiddlewareMixin

from cms.conf import defaults
from cms.models import (
    PublicationManagementError,
    path_token_generator,
    publication_manager,
)


class PublicationMiddleware(MiddlewareMixin):

    '''Middleware that enables preview mode for admin users.'''

    def process_request(self, request):
        '''Starts preview mode, if available.'''

        exclude_urls = [
            re.compile(url)
            for url in defaults.PUBLICATION_MIDDLEWARE_EXCLUDE_URLS
        ]

        if not any(pattern.match(request.path) for pattern in exclude_urls):
            # See if preview mode is requested.
            try:
                path = f'{request.path_info[1:] if request.path_info[1:] else request.path_info}'
                # Check for the value of 'preview' matching the token for the
                # current path. This is intended to throw KeyError if is not
                # present.
                token_preview_valid = path_token_generator.check_token(request.GET['preview'], path)
                # Allow something like preview=1, preview=any_other_value if
                # they are a staff user.
                user_preview = request.GET['preview'] and request.user.is_staff
            except KeyError:
                # Preview mode was not requested.
                user_preview = False
                token_preview_valid = False

            # Only allow preview mode if the user is a logged in administrator
            # or they have a token for this specific path.
            preview_mode = token_preview_valid or user_preview
            publication_manager.begin(not preview_mode)

    def process_response(self, request, response):
        '''Cleans up after preview mode.'''
        # Render the response if we're in a block of publication management.
        if publication_manager.select_published_active():
            if isinstance(response, SimpleTemplateResponse):
                response = response.render()
        # Clean up all blocks.
        while True:
            try:
                publication_manager.end()
            except PublicationManagementError:
                break
        # Carry on as normal.
        return response

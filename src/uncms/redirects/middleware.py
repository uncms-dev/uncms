from uncms.redirects.models import Redirect


class RedirectFallbackMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only 404s are worth checking; anything else (including 410) should
        # be assumed to be intentional.
        if response.status_code != 404:
            return response

        redirect = Redirect.objects.get_for_path(request.path)

        # Try removing or adding the trailing slash.
        if redirect is None:
            if request.path.endswith("/"):
                redirect = Redirect.objects.get_for_path(request.path[:-1])
            else:
                redirect = Redirect.objects.get_for_path("{}/".format(request.path))

        if redirect is not None:
            return redirect.response_for_path(request.path)

        # No redirect was found. Return the original response.
        return response

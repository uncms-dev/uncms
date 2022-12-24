from django.apps import apps
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.views.generic import RedirectView
from sorl.thumbnail import get_thumbnail

from uncms.conf import defaults
from uncms.models.base import path_token_generator


class AdminFileRedirectView(UserPassesTestMixin, RedirectView):
    """
    AdminMediaRedirectView redirects to the File object given in the keyword
    argument `pk`. It is intended for temporary image references in the HTML
    editor in the admin, which can later be switched out on the front-end with
    a real image URL. This allows changing the image later on without needing
    to edit every HTML page that has it embedded.
    """

    def test_func(self):
        return (
            self.request.user.is_authenticated and
            self.request.user.is_staff and
            self.request.user.has_perm('media.view_file')
        )

    def get_redirect_url(self, *args, **kwargs):
        obj = get_object_or_404(apps.get_model(defaults.MEDIA_FILE_MODEL), pk=kwargs['pk'])
        return obj.get_absolute_url()


class ImageView(RedirectView):
    """
    ImageView displays an image, taking sizing, format, colorspace and crop
    parameters from the "width"/"height", "format", "colorspace", and "crop"
    keyword arguments.

    One of "width" and "height" must be specified as integers. The other, if
    not an integer, must be "auto". If both are specified, "crop" may be
    specified as a valid sorl-thumbnail crop parameter, but may be "none"
    (which will behave as "center" if both width and height are specified).

    "colorspace" may be "auto", to preserve the image's original colour space,
    or some valid sorl-thumbnail colourspace.

    "format" may be "source", to preserve the image's original colour space,
    or some format accepted by sorl-thumbnail in lower-case.

    "quality" may be "default", using sorl's default image quality, or an
    integer.

    This is adapted from django-lazy-image by Dan Gamble. The whole approach
    of out-of-request-cycle thumbnailing was stolen from this package, and
    this file started life as a copy-paste from that project because the ideas
    were good. <https://github.com/dan-gamble/django-lazy-image>
    """

    # If they change the source image, we don't want to be showing the old
    # one. Sorl uses memcached to retrieve images with the same args, so this
    # should be pretty quick.
    permanent = False

    def dispatch(self, request, *args, **kwargs):
        # Check signature first to guard against enumerating media file IDs.
        signature = self.request.GET.get('signature')
        if not path_token_generator.check_token(signature, self.request.path):
            return HttpResponseBadRequest('Bad signature.')
        return super().dispatch(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        obj = get_object_or_404(apps.get_model(defaults.MEDIA_FILE_MODEL), pk=kwargs['pk'])

        # This should never be called on something that is not an image.
        # However, this can happen if a reference to a file was originally an
        # image, then its file was changed to something non-image later on.
        if not obj.is_image():
            raise Http404

        sorl_args = [obj.file]
        sorl_kwargs = {}

        width = kwargs['width']
        height = kwargs['height']
        colorspace = kwargs['colorspace']

        if width == 'auto':
            dimensions = 'x{}'.format(height)
        elif height == 'auto':
            dimensions = width
        else:
            dimensions = '{}x{}'.format(width, height)

            # If we have specified width and height, it is because we want a
            # specific aspect ratio. It must be cropped, and so if we haven't
            # specified any opinion on cropping origin, we should pick
            # 'center'
            if kwargs['crop'] == 'none':
                kwargs['crop'] = 'center'

        sorl_args.append(dimensions)

        if colorspace != 'auto':
            sorl_kwargs['colorspace'] = colorspace

        if kwargs['crop'] != 'none':
            sorl_kwargs['crop'] = kwargs['crop']

        if kwargs['format'] != 'source':
            sorl_kwargs['format'] = kwargs['format'].upper()

        if kwargs['quality'] != 'default':
            sorl_kwargs['quality'] = int(kwargs['quality'])

        # sorl should be allowed to fail loudly here; there is no reasonable
        # way to fail
        return get_thumbnail(*sorl_args, **sorl_kwargs).url

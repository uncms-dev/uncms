from django.http import HttpResponseForbidden, JsonResponse
from django.views.generic import View

from uncms.media.filetypes import IMAGE_DB_QUERY
from uncms.media.forms import ImageUploadForm


class ImageListAPIView(View):
    """
    A view which gives a JSON-serialised list of images for staff users. This
    is intended for the WYSIWYG text editor, but could be used for other
    things.
    """

    def dispatch(self, request, *args, **kwargs):
        # pylint:disable-next=attribute-defined-outside-init
        self.model_admin = kwargs["model_admin"]
        if not self.model_admin.has_view_permission(request):
            return HttpResponseForbidden("Forbidden")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return JsonResponse(
            [
                {
                    "title": obj.title,
                    "url": obj.get_temporary_url(),
                    "thumbnail": obj.get_admin_thumbnail().url,
                    "altText": obj.alt_text,
                }
                for obj in self.model_admin.get_queryset(request).filter(IMAGE_DB_QUERY)
            ],
            # Django complains that returning a list as the outer element is
            # not safe. Back in the day this was exploitable. This has not
            # worked with any browser for the last 20 years. Today it is a
            # perfectly safe thing to do.
            safe=False,
        )


class EditorImageUploadAPIView(View):
    """
    An image uploading view made specifically for the Trumbowyg image uploader
    plugin for the rich text editor in the admin.
    """

    def dispatch(self, request, *args, **kwargs):
        # pylint:disable-next=attribute-defined-outside-init
        self.model_admin = kwargs["model_admin"]
        if not self.model_admin.has_add_permission(request):
            return HttpResponseForbidden(b"Forbidden")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = ImageUploadForm(
            data=request.POST, files=request.FILES, user=request.user
        )
        if not form.is_valid():
            return JsonResponse(
                {
                    "success": False,
                    "detail": form.errors.get_json_data(),
                }
            )

        form.save()
        return JsonResponse(
            {
                "success": True,
                "file": form.instance.get_temporary_url(),
            }
        )

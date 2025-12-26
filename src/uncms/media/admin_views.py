from django.http import HttpResponseForbidden, JsonResponse
from django.template.defaultfilters import filesizeformat
from django.views.generic import View

from uncms.admin import get_admin_url
from uncms.media.filetypes import IMAGE_DB_QUERY
from uncms.media.forms import BulkUploadForm, ImageUploadForm
from uncms.media.models import Label

# Label name for files uploaded via bulk upload interface.
# Not translated to avoid different labels per admin language.
BULK_UPLOAD_LABEL_NAME = "Bulk upload"


class ImageListAPIView(View):
    """
    A view which gives a JSON-serialised list of images for staff users. This
    is intended for the WYSIWYG text editor, but could be used for other
    things.
    """

    def dispatch(self, request, *args, **kwargs):
        self.model_admin = kwargs["model_admin"]
        if not self.model_admin.has_view_permission(request):
            return HttpResponseForbidden(b"Forbidden")
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


class BulkUploadAPIView(View):
    """
    A view for uploading individual files as part of the bulk upload interface.
    This differs from the EditorImageUploadAPIView because the response can
    be formatted as we want it to be, and it also guesses a title for the
    image.
    """

    http_method_names = ["post"]

    def dispatch(self, request, *args, **kwargs):
        self.model_admin = kwargs["model_admin"]
        if not self.model_admin.can_bulk_add(request):
            return HttpResponseForbidden(b"Forbidden")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = BulkUploadForm(data=request.POST, files=request.FILES, user=request.user)
        if not form.is_valid():
            errors = form.errors.as_data()
            # Extract all error messages from all fields into a flat list.
            error_messages = [
                msg
                for field_errors in errors.values()
                for error in field_errors
                for msg in error.messages
            ]

            return JsonResponse(
                {
                    "error": (
                        " ".join(error_messages) if error_messages else "Invalid file"
                    )
                },
                status=400,
            )

        instance = form.save()
        instance.labels.add(Label.objects.get_or_create(name=BULK_UPLOAD_LABEL_NAME)[0])

        file_size = instance.file.size

        response = {
            "name": instance.title,
            "size": file_size,
            "sizeFormatted": filesizeformat(file_size),
        }

        if instance.is_image():
            response["thumbnail"] = instance.get_admin_thumbnail().url
        else:
            response["thumbnail"] = None

        if self.model_admin.has_view_permission(request, obj=instance):
            response["adminUrl"] = get_admin_url(instance)

        return JsonResponse(response)

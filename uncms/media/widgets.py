from django.apps import apps
from django.contrib.admin.widgets import ForeignKeyRawIdWidget

from uncms.conf import defaults


class ImageThumbnailWidget(ForeignKeyRawIdWidget):
    '''
    A widget used to display a thumbnail image preview
    '''
    template_name = 'admin/widgets/image_raw_id.html'

    def get_context(self, name, value, attrs):
        file_model = apps.get_model(defaults.MEDIA_FILE_MODEL)

        context = super().get_context(name, value, attrs)
        if value:
            context['file_obj'] = file_model.objects.get(pk=value)
        return context

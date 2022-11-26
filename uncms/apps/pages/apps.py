from django.apps import AppConfig
from watson import search as watson


class PagesAppConfig(AppConfig):
    name = 'uncms.apps.pages'

    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        from uncms.apps.pages.models import PageSearchAdapter  # pylint:disable=import-outside-toplevel
        Page = self.get_model('Page')
        watson.register(Page, PageSearchAdapter)

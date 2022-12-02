from django.apps import AppConfig


class UnCMSAppConfig(AppConfig):
    name = 'uncms'
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        # import used for the side effect of registering checks
        from uncms import checks  # pylint:disable=unused-import,import-outside-toplevel  # noqa

from django.apps import AppConfig


class UnCMSAppConfig(AppConfig):
    """
    Why is this in here? Well, historically everything lived under "cms.apps"
    but the "apps" name later got taken by Django's default app config
    discovery. Oh well! This will do!
    """
    name = 'uncms'
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        # import used for the side effect of registering checks
        from uncms import checks  # pylint:disable=unused-import,import-outside-toplevel  # noqa

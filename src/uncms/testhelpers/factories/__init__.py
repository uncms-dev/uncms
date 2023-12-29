import factory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory

from uncms.pages.middleware import RequestPageManager


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Sequence(lambda n: f"user{n}")
    password = "insecure"

    class Meta:
        model = get_user_model()

    class Params:
        superuser = factory.Trait(
            is_staff=True,
            is_superuser=True,
        )

    @factory.post_generation
    def permissions(self, created, extracted, **kwargs):
        if extracted:
            for permission in extracted:
                app_label, permission_name = permission.split(".")
                self.user_permissions.add(
                    Permission.objects.get(
                        content_type__app_label=app_label,
                        codename=permission_name,
                    )
                )


class AdminRequestFactory(RequestFactory):
    """
    A subclass of RequestFactory which sets the session and _messages
    attributes required for doing anything with Django admin views.
    """

    def request(self, **request):
        req = super().request(**request)
        req.session = "session"
        req._messages = FallbackStorage(req)
        req.pages = RequestPageManager(req)
        return req

import factory
from django.contrib.auth import get_user_model


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Sequence(lambda n: 'user{n}')
    password = 'insecure'

    class Meta:
        model = get_user_model()

    class Params:
        superuser = factory.Trait(
            is_staff=True,
            is_superuser=True,
        )

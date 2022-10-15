import factory
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify
from watson import search as watson

from cms.apps.pages.models import Page
from cms.apps.testing_models.models import EmptyTestPage


class PageFactory(factory.django.DjangoModelFactory):
    """
    PageFactory gives an easy way of creating pages. Instantiate it with
    the "content" parameter as an unsaved ContentBase derivative and it will
    handle the specifics of saving the content to the page, including making
    sure that Watson doesn't attempt to read the page until both the page and
    its content are saved.

    `content` is optional; if it is omitted you will get an EmptyTestPage
    as the page content, which is a content model with no fields.
    """
    title = factory.Sequence(lambda n: f'Page {n}')

    slug = factory.LazyAttribute(lambda o: slugify(o.title))

    @factory.post_generation
    def content(self, create, extracted, **kwargs):
        extracted.page = self
        extracted.save()

    class Meta:
        model = Page

    @classmethod
    def _generate(cls, strategy, params):
        if not 'content' in params:
            params['content'] = EmptyTestPage()
        params['content_type'] = ContentType.objects.get_for_model(params['content'].__class__)
        with watson.update_index():
            return super()._generate(strategy, params)

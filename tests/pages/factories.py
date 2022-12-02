import factory
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify
from watson import search as watson

from tests.testing_app.models import EmptyTestPage
from uncms.pages.models import Page


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
        if 'content' not in params:
            params['content'] = EmptyTestPage()
        params['content_type'] = ContentType.objects.get_for_model(params['content'].__class__)
        with watson.update_index():
            return super()._generate(strategy, params)

    @classmethod
    def create_tree(cls, *shape):
        """
        PageFactory.create_tree creates a page tree for testing things at
        depth.

        `shape` takes the form:

        top_level_depth, sub_menu_depth, sub_sub_menu_depth, ...

        So if you want to create a menu of 5 top level pages (underneath the
        home page), each of which has 4 children, each of *those* having 7
        children each, this would do the trick:

        PageFactory.create_tree(5, 4, 7)
        """
        homepage = cls.create()

        def create_children_recursive(parent, nested_shape):
            if not nested_shape:
                return

            for _ in range(nested_shape[0]):
                page = cls.create(parent=parent)
                create_children_recursive(page, nested_shape[1:])

        create_children_recursive(homepage, shape)

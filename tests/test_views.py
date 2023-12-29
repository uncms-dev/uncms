from django.views import generic

from uncms.views import SearchMetaDetailMixin, TextTemplateView


def test_texttemplateview_render_to_response():
    view = TextTemplateView()
    view.request = {}
    view.template_name = "templates/base.html"

    rendered = view.render_to_response({})

    assert rendered.template_name == ["templates/base.html"]
    assert rendered["Content-Type"] == "text/plain; charset=utf-8"
    assert rendered.status_code == 200


def test_searchmetadetailmixin_get_context_data():
    class Obj:
        def get_context_data(self):
            return {"foo": "bar"}

    class TestClass(SearchMetaDetailMixin, generic.DetailView):
        object = Obj()

    context = TestClass().get_context_data()
    assert "foo" in context
    assert context["foo"] == "bar"

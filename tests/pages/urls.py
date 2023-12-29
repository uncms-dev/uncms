from django.http import Http404, HttpResponse
from django.urls import path


def hello_view(request):
    return HttpResponse("Hello!")


def not_found_view(request):
    raise Http404("CANARY")


def detail_view(request, *args, **kwargs):
    return HttpResponse(f'detail view: {kwargs["slug"]}')


def broken_view(request):
    return None


urlpatterns = [
    path("", hello_view, name="index"),
    path("404/", not_found_view, name="not_found"),
    path("broken/", broken_view, name="broken_view"),
    path("<slug:slug>/", detail_view, name="detail"),
]

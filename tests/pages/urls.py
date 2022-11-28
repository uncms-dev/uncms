from django.http import Http404, HttpResponse
from django.urls import path


def view(request, *args, **kwargs):
    if request.path == '/raise404/':
        raise Http404
    return HttpResponse('Hello!')


urlpatterns = [
    path('', view, name='index'),
    path('<slug:slug>/', view, name='detail'),
]

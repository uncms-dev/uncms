'''URLs used by ContentBase derivatives.'''

from django.urls import path
from django.views.decorators.csrf import csrf_protect

from cms.apps.pages import views

urlpatterns = [
    path('', csrf_protect(views.ContentIndexView.as_view()), name='index'),
]

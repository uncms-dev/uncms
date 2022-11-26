'''URLs used by the links application.'''

from django.urls import path

from uncms.apps.links.views import index

urlpatterns = [
    path('', index, name='index'),
]

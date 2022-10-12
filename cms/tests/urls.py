from django.conf import settings
from django.contrib import admin
from django.contrib.contenttypes.views import shortcut
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('library/', include('cms.apps.media.urls', namespace='media_library')),
    path('r/<int:content_type_id>-<int:object_id>/', shortcut, name='permalink_redirect'),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT})
]

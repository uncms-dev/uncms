from django.contrib import admin
from django.contrib.contenttypes.views import shortcut
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('<int:content_type_id>-<int:object_id>/', shortcut, name='permalink_redirect'),
]

from django.urls import path

from cms.apps.media.views import ImageView

app_name = 'media'

urlpatterns = [
    path(
        '<int:pk>/width:<str:width>/height:<str:height>/fmt:<str:format>/color:<str:colorspace>/q:<str:quality>/crop:<str:crop>/',
        ImageView.as_view(),
        name='image_view',
    ),
]

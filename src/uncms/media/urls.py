from django.urls import path

from uncms.media.views import AdminFileRedirectView, ImageView

app_name = 'media'

urlpatterns = [
    path(
        '<int:pk>/width:<str:width>/height:<str:height>/fmt:<str:format>/color:<str:colorspace>/q:<str:quality>/crop:<str:crop>/',
        ImageView.as_view(),
        name='image_view',
    ),
    path('redirect/<int:pk>/', AdminFileRedirectView.as_view(), name='file_redirect'),
]

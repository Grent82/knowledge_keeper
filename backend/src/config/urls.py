from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/access/", include("apps.access_control.urls")),
    path("api/media/", include("apps.media_library.urls")),
    path("api/playback/", include("apps.playback.urls")),
    path("api/system/", include("apps.system.urls")),
]

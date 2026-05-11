from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/access/", include("apps.access_control.urls")),
    path("api/media/", include("apps.media_library.urls")),
    path("api/playback/", include("apps.playback.urls")),
    path("api/knowledge-notes/", include("apps.knowledge_notes.urls")),
    path("api/system/", include("apps.system.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

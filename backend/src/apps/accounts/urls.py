from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import LoginView, LogoutView, RestrictedUserViewSet, SessionView

router = SimpleRouter(trailing_slash=False)
router.register("restricted-users", RestrictedUserViewSet, basename="restricted-user")

urlpatterns = [
    path("login", LoginView.as_view(), name="auth-login"),
    path("logout", LogoutView.as_view(), name="auth-logout"),
    path("session", SessionView.as_view(), name="auth-session"),
    *router.urls,
]

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.common.permissions import IsOwnerRole

from .models import User, UserRole
from .serializers import (
    LoginSerializer,
    RestrictedUserSerializer,
    SessionSerializer,
    logout_user,
)


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list[type] = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(SessionSerializer.from_user(user), status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list[type] = []

    def post(self, request):
        logout_user(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class SessionView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(SessionSerializer.from_user(request.user), status=status.HTTP_200_OK)


class RestrictedUserViewSet(ModelViewSet):
    serializer_class = RestrictedUserSerializer
    permission_classes = [IsOwnerRole]
    queryset = User.objects.filter(role=UserRole.RESTRICTED_USER).order_by("username")

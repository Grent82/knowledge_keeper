from django.contrib.auth import authenticate, login, logout
from rest_framework import serializers

from .models import User, UserRole


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        request = self.context["request"]
        user = authenticate(
            request=request,
            username=attrs["username"],
            password=attrs["password"],
        )
        if user is None:
            raise serializers.ValidationError("Invalid username or password.")
        attrs["user"] = user
        return attrs

    def save(self):
        request = self.context["request"]
        user = self.validated_data["user"]
        login(request, user)
        return user


class SessionSerializer(serializers.Serializer):
    is_authenticated = serializers.BooleanField()
    username = serializers.CharField(allow_blank=True)
    role = serializers.CharField(allow_blank=True)

    @classmethod
    def from_user(cls, user):
        if user.is_authenticated:
            return {
                "is_authenticated": True,
                "username": user.username,
                "role": user.role,
            }
        return {"is_authenticated": False, "username": "", "role": ""}


def logout_user(request) -> None:
    logout(request)


class RestrictedUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["id", "username", "password", "email", "is_active", "role"]
        read_only_fields = ["id", "role"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        return User.objects.create_user(
            password=password,
            role=UserRole.RESTRICTED_USER,
            **validated_data,
        )

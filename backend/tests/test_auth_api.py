import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole

pytestmark = pytest.mark.django_db


def test_login_session_and_logout_flow():
    User.objects.create_user(username="owner-login", password="secret", role=UserRole.OWNER)
    client = APIClient()

    login_response = client.post(
        "/api/auth/login",
        {"username": "owner-login", "password": "secret"},
        format="json",
    )

    assert login_response.status_code == 200
    assert login_response.data["is_authenticated"] is True
    assert login_response.data["role"] == UserRole.OWNER

    session_response = client.get("/api/auth/session")

    assert session_response.status_code == 200
    assert session_response.data["is_authenticated"] is True
    assert session_response.data["username"] == "owner-login"

    logout_response = client.post("/api/auth/logout")

    assert logout_response.status_code == 204


def test_login_rejects_invalid_credentials():
    User.objects.create_user(username="owner-login-2", password="secret")
    client = APIClient()

    response = client.post(
        "/api/auth/login",
        {"username": "owner-login-2", "password": "wrong"},
        format="json",
    )

    assert response.status_code == 400


def test_owner_can_create_restricted_user():
    owner = User.objects.create_user(
        username="owner-manage-users",
        password="secret",
        role=UserRole.OWNER,
    )
    client = APIClient()
    client.force_authenticate(user=owner)

    response = client.post(
        "/api/auth/restricted-users",
        {
            "username": "guest-user",
            "password": "secret",
            "email": "guest@example.com",
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data["username"] == "guest-user"
    assert response.data["role"] == UserRole.RESTRICTED_USER

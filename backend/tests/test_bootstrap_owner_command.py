import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.accounts.models import User, UserRole

pytestmark = pytest.mark.django_db


def test_bootstrap_owner_command_creates_owner(capsys):
    call_command("bootstrap_owner", username="owner", password="secret", email="owner@example.com")

    user = User.objects.get(username="owner")

    assert user.role == UserRole.OWNER
    assert user.is_staff is True
    assert user.is_superuser is True


def test_bootstrap_owner_command_rejects_existing_user():
    User.objects.create_user(username="owner", password="secret", role=UserRole.OWNER)

    with pytest.raises(CommandError):
        call_command("bootstrap_owner", username="owner", password="secret")

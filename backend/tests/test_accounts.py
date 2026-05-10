from apps.accounts.models import User, UserRole


def test_user_defaults_to_owner_role():
    user = User(username="owner")

    assert user.role == UserRole.OWNER
    assert user.is_owner is True
    assert user.is_restricted_user is False


def test_restricted_user_helper_flags():
    user = User(username="guest", role=UserRole.RESTRICTED_USER)

    assert user.is_owner is False
    assert user.is_restricted_user is True

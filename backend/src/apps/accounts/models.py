from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    OWNER = "owner", "Owner"
    RESTRICTED_USER = "restricted_user", "Restricted User"


class User(AbstractUser):
    role = models.CharField(
        max_length=32,
        choices=UserRole.choices,
        default=UserRole.OWNER,
        help_text="Application-level access role used for visibility and management rules.",
    )

    @property
    def is_owner(self) -> bool:
        return self.role == UserRole.OWNER

    @property
    def is_restricted_user(self) -> bool:
        return self.role == UserRole.RESTRICTED_USER

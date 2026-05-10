from rest_framework.permissions import BasePermission


class IsOwnerRole(BasePermission):
    message = "Only owner accounts can perform this action."

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, "is_owner", False))

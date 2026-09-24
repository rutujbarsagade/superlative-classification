"""Model-level permissions."""

from rest_framework.permissions import BasePermission

from apps.accounts.permissions import can_access_platform
from apps.accounts.models import UserRole

from .models import MLModel


def can_manage_model(user, model: MLModel) -> bool:
    if not can_access_platform(user):
        return False
    return user.role == UserRole.SUPER_ADMIN or model.owner_id == user.pk


class IsModelOwnerOrSuperAdmin(BasePermission):
    message = "You do not have permission to manage this model."

    def has_object_permission(self, request, view, obj) -> bool:
        return can_manage_model(request.user, obj)

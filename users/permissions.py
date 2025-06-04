from rest_framework import permissions
from django.contrib.auth.models import Group


class IsAdminGroupUser(permissions.BasePermission):

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and Group.objects.filter(
                name="Admin", custom_user_set=request.user
            ).exists()
        )

from rest_framework.permissions import BasePermission

class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.groups.filter(name='admin').exists()


class IsOrganizer(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.groups.filter(name='organizer').exists()


class IsAdminOrSuperUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_superuser or
            request.user.groups.filter(name='admin').exists()
        )


class IsOrganizerOrAdminOrSuperUser(BasePermission):
    """
    Organizer boleh jika objek event adalah miliknya
    Admin & Superuser boleh semua
    """
    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_authenticated and (
            request.user.is_superuser or
            request.user.groups.filter(name='admin').exists() or
            getattr(obj, 'organizer', None) == request.user
        )

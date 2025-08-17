from rest_framework.permissions import BasePermission

class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
            request.user.is_superuser

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
            request.user.groups.filter(name='admin').exists()

class IsOrganizer(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated \
            and request.user.groups.filter(name='organizer').exists()

class IsAdminOrSuperUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_superuser or
            request.user.groups.filter(name='admin').exists()
        )

class IsOwnerOrAdminOrSuperUser(BasePermission):
    """
    Superuser, staff (is_staff=True), atau user dalam group 'admin'
    bebas akses.
    Organizer hanya boleh jika event adalah miliknya (obj.organizer_id == user).
    """
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        # superuser & admin group full access
        if user.is_superuser or user.is_staff or user.groups.filter(name="admin").exists():
            return True

        # cek kepemilikan event (organizer)
        if hasattr(obj, "organizer_id"):
            return obj.organizer_id == user
        
        return False
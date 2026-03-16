from rest_framework import permissions

class IsOwnerOrAdminOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # 1. Always allow Admins
        if request.user and request.user.is_staff:
            return True
        
        # 2. Allow Read-only for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # 3. For Update/Delete, check if the user is the owner
        # Assumes your model has a 'user' field
        return obj.user == request.user
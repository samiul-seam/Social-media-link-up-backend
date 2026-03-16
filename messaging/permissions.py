from rest_framework import permissions

class IsSenderOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.sender == request.user
    
    
class IsParticipantOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        return request.user in [obj.user1, obj.user2]
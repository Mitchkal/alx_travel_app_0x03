from rest_framework.permissions import BasePermission, SAFE_METHODS

"""
custom permission to allow hots of a listing to edit or delete it
"""

class IsOwnerOrReadOnly(BasePermission):
    """
    custom permission to allow only 
    the owners of an object to edit it
    """
    def has_object_permission(self, request, view, obj):
        """
        Read permissions for any request
        We allow GET, HEAD, or OPTIONS requests
        """
        if request.method in SAFE_METHODS:
            return True

        # write permissions for host of listing
        return obj.owner == request.user

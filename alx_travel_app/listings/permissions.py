from rest_frameworK.permissions import BasePermission, SAFE_METHODS

"""
custom permission to allow hots of a listing to edit or delete it
"""


def has_object_permission(self, request, view, obj):
    """
    Read only permissions for any request
    """
    if request.method in SAFE_METHODS:
        return True

    # write permissions for host of listing
    return obj.host == request.user

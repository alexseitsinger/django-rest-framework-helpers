from rest_framework import permissions

class IsUser(permissions.BasePermission):
    """ Return True if the obj is the same User object."""
    def has_object_permission(self, request, view, obj):
        return request.user == obj

class AllowNone(permissions.BasePermission):
    def has_permission(self, request, view):
        return False

    def has_object_permission(self, request, view, obj):
        return False

class IsAnonymous(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_anonymous()

class IsListAction(permissions.BasePermission):
    def has_permission(self, request, view):
        return view.action == "list"

class IsRetrieveAction(permissions.BasePermission):
    def has_permission(self, request, view):
        return view.action == "retrieve"

class IsCreateAction(permissions.BasePermission):
    def has_permission(self, request, view):
        return view.action == "create"

class IsUpdateAction(permissions.BasePermission):
    def has_permission(self, request, view):
        return view.action == "update"

class IsPartialUpdateAction(permissions.BasePermission):
    def has_permission(self, request, view):
        return view.action == "partial_update"


class IsObjectUser(permissions.BasePermission):
    """ Permission that only allows the obj's user to access it. """
    def has_object_permission(self, request, view, obj):
        return bool(obj.user == request.user)

class NestedUserFieldPermission(permissions.BasePermission):
    nested_user_field = None

    def has_object_permission(self, request, view, obj):
        attr = obj
        for name in self.nested_user_field.split("."):
            attr = getattr(attr, name)
        if request.user == attr:
            return True
        return False

class IsObjectUserAttribute(permissions.BasePermission):
    """ Permission that only allows the obj's user to access it. """

    @classmethod
    def create(cls, attrs):
        instance = cls
        instance.object_user_attrs = attrs
        return instance

    def has_object_permission(self, request, view, obj):
        ouas = self.object_user_attrs

        if ouas is None:
            return False

        for string in ouas:
            attr = obj
            for name in string.split("."):
                attr = getattr(attr, name)
            if request.user == attr:
                return True

        return False

class IsPostRequest(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method == "POST"

class IsPutRequest(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method == "PUT"

class IsPatchRequest(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method == "PATCH"

class IsReadOnlyRequest(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS

class HasQueryParams(permissions.BasePermission):
    # def __init__(self, *params):
    #     self.query_params_required = params

    def has_permission(self, request, view):
        return len(request.query_params) > 0


class PublicEndpoint(permissions.BasePermission):
    def has_permission(self, request, view):
        return True


class IsStaffOrTargetUser(permissions.BasePermission):
    def has_permission(self, request, view):
        # allow user to list all users if logged in user is staff
        return view.action == 'retrieve' or request.user.is_staff

    def has_object_permission(self, request, view, obj):
        # allow logged in user to view own details, allows staff to view all records
        return request.user.is_staff or obj == request.user


class IsUserOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has a `user` attribute.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Instance must have an attribute named `owner`.
        if request.user == obj:
            return True

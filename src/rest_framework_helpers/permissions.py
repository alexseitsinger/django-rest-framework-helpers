import os
import re
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsRelated(BasePermission):
    """
    Returns True if the current requesting user matches the target object, target field,
    or exists in the target fields objects.
    """

    target_field = None

    def get_field(self, obj):
        if self.target_field is None:
            return None
        bits = self.target_field.split(".")
        field = obj
        for bit in bits:
            field = getattr(field, bit, None)

    def is_related(self, user, obj):
        # If it's a user object instance, compare it directly.
        if user == obj:
            return True
        # Compare the field, otherwise.
        field = self.get_field(obj)
        if field is None:
            return False
        if user == field or user in field.all():
            return True
        # Else, return False
        return False

    def has_object_permission(self, request, view, obj):
        return self.is_related(request.user, obj)


class AllowNone(BasePermission):
    """
    Always returns False
    """

    def has_permission(self, request, view):
        return False

    def has_object_permission(self, request, view, obj):
        return False


class IsAnonymous(BasePermission):
    """
    Returns True if the current requesting user is anonymous.
    """

    def is_anonymous(self, request):
        return request.user.is_anonymous()

    def has_permission(self, request, view):
        return self.is_anonymous(request)


class IsAction(BasePermission):
    """
    Returns True if the view action matches the specified action.
    """

    target_action = None

    def is_action(self, view):
        target_action = self.target_action
        if target_action is None:
            return False
        return view.action == target_action

    def has_permission(self, request, view):
        return self.is_action(view)


class IsListAction(IsAction):
    target_action = "list"


class IsRetrieveAction(IsAction):
    target_action = "retrieve"


class IsCreateAction(IsAction):
    target_action = "create"


class IsUpdateAction(IsAction):
    target_action = "update"


class IsPartialUpdateAction(IsAction):
    target_action = "partial_update"


class IsDestroyAction(IsAction):
    target_action = "destroy"


class IsMethod(BasePermission):
    """
    Returns True if the request method matches the target method.
    """

    target_method = None

    def is_method(self, request):
        target_method = self.target_method
        if target_method is None:
            return False
        return request.method == target_method

    def has_permission(self, request, view):
        return self.is_method(request)


class IsPostMethod(IsMethod):
    target_method = "POST"


class IsPutMethod(IsMethod):
    target_method = "PUT"


class IsPatchMethod(IsMethod):
    target_method = "PATCH"


class IsDeleteMethod(IsMethod):
    target_method = "DELETE"


class IsGetMethod(IsMethod):
    target_method = "GET"


class IsOptionsMethod(IsMethod):
    target_method = "OPTIONS"


class IsHeadMethod(IsMethod):
    target_method = "HEAD"


class IsReadOnlyRequest(BasePermission):
    """
    Return True if the request method is one of GET, HEAD, OPTIONS
    """

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class HasQueryParams(BasePermission):
    """
    Returns True if specific query params are present in the request.
    """

    target_params = None

    def has_params(self, request):
        request_params = request.query_params
        target_params = self.target_params
        if len(request.query_params) == 0:
            return False
        if target_params is None:
            return False
        result = True
        for k, v in target_params.items():
            if result is False:
                continue
            if k not in request_params or request_params[k] != v:
                result = False
        return result

    def has_permission(self, request, view):
        return self.has_params(request)


class ReadOnlyExceptForStaff(BasePermission):
    """
    Returns True if the action is retrieve, or the user is staff.
    Returns True if the user is staff or the object matches the requesting user.
    """

    def has_permission(self, request, view):
        # allow user to list all users if logged in user is staff
        return view.action == "retrieve" or request.user.is_staff

    def has_object_permission(self, request, view, obj):
        # allow logged in user to view own details, allows staff to view all records
        return request.user.is_staff or obj == request.user


class HasAllowedReferer(BasePermission):
    """
    Returns True if the request's referer matches one of the accepted referers.
    """

    allowed_prefixes = None
    allowed_suffixes = None

    def get_allowed_referers(self):
        prefixes = self.allowed_prefixes
        suffixes = self.allowed_suffixes
        if any([x is None for x in [prefixes, suffixes]]):
            return None
        result = []
        regex = r"(https?://)(.*)"
        for prefix in prefixes:
            try:
                protocol, base = re.match(regex, prefix).groups()
                for suffix in suffixes:
                    normalized = os.path.normpath("{}/{}".format(base, suffix))
                    full = "{}{}".format(protocol, normalized)
                    result.append(full)
                    if not full.endswith("/"):
                        result.append("{}/".format(full))
            except AttributeError:
                pass
        return result

    def has_allowed_referer(self, request):
        referer = request.META.get("HTTP_REFERER", None)
        allowed = self.get_allowed_referers()
        if any([x is None for x in [referer, allowed]]):
            return False
        if referer in allowed:
            return True
        return False

    def has_permission(self, request, view):
        return self.has_allowed_referer(request)


class HasAllowedUserAgent(BasePermission):
    """
    Returns True if the request's user agent matches one of the allowed user agents.
    """

    user_agents_allowed = None

    def get_user_agents_allowed(self):
        allowed = self.user_agents_allowed
        return allowed

    def has_allowed_user_agent(self, request):
        current = request.META.get("HTTP_USER_AGENT", None)
        allowed = self.get_user_agents_allowed()
        if any([x is None for x in [current, allowed]]):
            return False
        if current in allowed:
            return True
        return False

    def has_permission(self, request, view):
        return self.has_allowed_user_agent(request)


class DoesNotHaveBlockedIPAddress(BasePermission):
    """
    Returns False if the IP address of the current request is specified as blocked.
    """

    ip_addresses_blocked = None
    fallback_result = False

    def get_ip_addresses_blocked(self):
        blocked = self.ip_addresses_blocked
        return blocked

    def has_blocked_ip_address(self, request):
        ip_address = request.META.get("REMOTE_ADDR", None)
        blocked = self.get_ip_addresses_blocked()
        if any([x is None for x in [ip_address, blocked]]):
            return self.fallback_result
        if ip_address in blocked:
            return True
        return self.fallback_result

    def has_permission(self, request, view):
        if self.has_blocked_ip_address(request) is True:
            return False
        return True


class HasAllowedIPAddress(BasePermission):
    """
    Return True only if the IP address of the current request is in the list.
    """

    ip_addresses_allowed = None

    def get_ip_addressed_allowed(self):
        allowed = self.ip_addresses_allowed
        return allowed

    def has_allowed_ip_address(self, request):
        ip_address = request.META.get("REMOTE_ADDR", None)
        allowed = self.get_ip_addresses_allowed()
        if any([x is None for x in [ip_address, allowed]]):
            return False
        if ip_address in allowed:
            return True
        return False

    def has_permission(self, request, view):
        return self.has_allowed_ip_address(request)

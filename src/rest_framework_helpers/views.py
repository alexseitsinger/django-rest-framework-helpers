from collections import OrderedDict
from rest_framework.reverse import reverse
from rest_framework.response import Response
from rest_framework.views import APIView


class APIRootView(APIView):
    endpoints = {}
    endpoints_seen = {}
    endpoints_created = None
    view_name_prefix = ""
    view_name_suffix = ""

    def is_endpoints_changed(self, endpoints, seen, created):
        changed = False
        if created is None:
            changed = True
        for name, view_name in endpoints.items():
            if changed is True:
                break
            if name not in seen or seen[name] != view_name:
                seen[name] = view_name
                changed = True
        return changed

    def get_full_view_name(self, name):
        prefix = self.view_name_prefix
        suffix = self.view_name_suffix
        if not name.startswith(prefix):
            if prefix.endswith(":"):
                prefix = prefix[:-1]
            name = "{}:{}".format(prefix, name)
        if not name.endswith(suffix):
            if suffix.startswith("-"):
                suffix = suffix[1:]
            name = "{}-{}".format(name, suffix)
        name = name.replace(r"-+", "-")
        name = name.replace(r":+", ":")
        return name

    def create_endpoints(self, request, format, endpoints):
        created = OrderedDict()
        for name, view_name in endpoints.items():
            full_view_name = self.get_full_view_name(view_name)
            created[name] = reverse(full_view_name, request=request, format=format)
        return created

    def get_endpoints(self, request, format):
        endpoints = self.endpoints
        seen = self.endpoints_seen
        created = self.endpoints_created
        changed = self.is_endpoints_changed(endpoints, seen, created)
        if changed is True:
            created = self.endpoints_created = self.create_endpoints(
                request, format, endpoints
            )
        return created

    def get(self, request, format=None):
        return Response(self.get_endpoints(request, format))

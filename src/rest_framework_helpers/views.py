from collections import OrderedDict
from rest_framework.reverse import reverse
from rest_framework.response import Response
from rest_framework.views import APIView


class APIRootView(APIView):
    endpoints = {}
    endpoints_seen = {}
    endpoints_created = None

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

    def create_endpoints(self, request, format, endpoints):
        created = OrderedDict()
        for name, view_name in endpoints.items():
            created[name] = reverse(view_name, request=request, format=format)
        return created

    def get_endpoints(self, request, format):
        endpoints = self.endpoints
        seen = self.endpoints_seen
        created = self.endpoints_created
        changed = self.is_endpoints_changed(endpoints, seen, created)
        if changed is True:
            created = self.created = self.create_endpoints(request, format, endpoints)
        return endpoints

    def get(self, request, format=None):
        return Response(self.get_endpoints(request, format))

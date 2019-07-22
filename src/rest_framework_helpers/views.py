from collections import OrderedDict
from rest_framework.reverse import reverse
from rest_framework.response import Response
from rest_framework.views import APIView


class APIRootView(APIView):
    views = {}
    views_seen = {}
    endpoints = None

    def is_views_changed(self, endpoints, views, seen):
        changed = False
        if endpoints is None:
            changed = True
        for name, view_name in views.items():
            if changed is True:
                break
            if name not in seen or seen[name] != view_name:
                seen[name] = view_name
                changed = True
        return changed

    def create_endpoints(self, request, format, views):
        endpoints = OrderedDict()
        for name, view_name in views.items():
            endpoints[name] = reverse(view_name, request=request, format=format)
        return endpoints

    def get_endpoints(self, request, format):
        endpoints = self.endpoints
        views = self.views
        seen = self.views_seen
        changed = self.is_views_changed(endpoints, views, seen)
        if changed is True:
            endpoints = self.endpoints = self.create_endpoints(request, format, views)
        return endpoints

    def get(self, request, format=None):
        return Response(self.get_endpoints(request, format))

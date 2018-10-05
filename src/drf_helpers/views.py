from django.conf import settings
from django.http import Http404
from collections import OrderedDict
from rest_framework.reverse import reverse
from rest_framework.response import Response
from rest_framework.views import APIView

class APIRootView(APIView):
    views = {}

    def create_endpoints(self, request, format):
        endpoints = OrderedDict()
        for endpoint_name, view_name in self.views.items():
            endpoints[endpoint_name] = reverse(
                view_name,
                request=request,
                format=format
            )
        return endpoints

    def get(self, request, format=None):
        if settings.IS_DEVELOPMENT:
            endpoints = self.create_endpoints(request, format)
            return Response(endpoints)
        else:
            raise Http404()

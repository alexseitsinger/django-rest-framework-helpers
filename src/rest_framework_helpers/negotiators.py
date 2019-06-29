"""
http://www.django-rest-framework.org/api-guide/content-negotiation/#setting-the-content-negotiation

https://stackoverflow.com/questions/45498989/django-rest-framework-output-in-json-to-the-browser-by-default

https://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html
"""
from rest_framework.negotiation import BaseContentNegotiation


class IgnoreClientContentNegotiation(BaseContentNegotiation):
    """
    A custom content negotiation class which ignores the client request when selecting the appropriate parser or renderer.
    """

    def select_parser(self, request, parsers):
        """
        Select the first parser in the `.parser_classes` list.
        """
        return parsers[0]

    def select_renderer(self, request, renderers, format_suffix):
        """
        Select the first renderer in the `.renderer_classes` list.
        """
        return (renderers[0], renderers[0].media_type)

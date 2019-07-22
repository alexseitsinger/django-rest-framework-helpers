"""
[The OPTIONS] method allows a client to determine the options and/or requirements
associated with a resource, or the capabilities of a server, without implying a resource
action or initiating a resource retrieval.
"""
from rest_framework.metadata import BaseMetadata


class NoMetaData(BaseMetadata):
    """
    A null metadata scheme that configures OPTIONS responses to be empty.

    To set that metadata class globally we can use the DEFAULT_METADATA_CLASS setting in
    Rest Framework:

    REST_FRAMEWORK = { 'DEFAULT_METADATA_CLASS': 'yourapp.metadata.NoMetaData' }

    https://dbader.org/blog/django-rest-framework-options-response
    """

    def determine_metadata(self, request, view):
        return None

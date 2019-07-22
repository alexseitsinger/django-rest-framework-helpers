from rest_framework.viewsets import ModelViewSet
from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet

from .mixins import ParameterisedViewMixin


class ParameterisedModelViewSet(ParameterisedViewMixin, ModelViewSet):
    pass


class CreateListRetrieveViewSet(
    CreateModelMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet
):
    """
    A viewset that provides "retrieve", "create", and "list" actions.

    To use it, override the class and set the ".queryset" and ".serializer_class"
    attributes"
    """

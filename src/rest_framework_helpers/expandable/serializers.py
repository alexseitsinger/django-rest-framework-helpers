from rest_framework.serializers import ModelSerializer, HyperlinkedModelSerializer
from .mixins import ExpandableModelSerializerMixin


class ExpandableHyperlinkedModelSerializer(
    ExpandableModelSerializerMixin, HyperlinkedModelSerializer
):
    pass


class ExpandableModelSerializer(ExpandableModelSerializerMixin, ModelSerializer):
    pass

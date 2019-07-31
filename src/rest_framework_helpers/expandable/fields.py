from rest_framework.serializers import SlugRelatedField, HyperlinkedRelatedField
from .mixins import ExpandableRelatedFieldMixin


class ExpandableHyperlinkedRelatedField(
    ExpandableRelatedFieldMixin, HyperlinkedRelatedField
):
    pass


class ExpandableSlugRelatedField(ExpandableRelatedFieldMixin, SlugRelatedField):
    pass

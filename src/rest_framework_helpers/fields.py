import base64
import six
import uuid
import pytz
import imghdr
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from django.utils.module_loading import import_string
from rest_framework.serializers import (
    Field,
    HyperlinkedRelatedField,
    HyperlinkedIdentityField,
    HyperlinkedModelSerializer,
    ImageField,
    ValidationError,
)

from .mixins import ParameterisedFieldMixin


class ExpandableHyperlinkedRelatedField(HyperlinkedRelatedField):
    """
    A serializer field that will output its real object when expanded.

    eg:
        GET http://www.example.com/api/v1/models/1?expand=field_name,field_name
    """

    expand_serializer = None

    def __init__(self, *args, **kwargs):
        if self.expand_serializer is None:
            self.expand_serializer = kwargs.pop("expand_serializer", None)
        super().__init__(*args, **kwargs)

    def to_representation(self, obj):
        ret = super().to_representation(obj)
        if self.expand_serializer is None:
            return ret
        context = getattr(self, "context", None)
        if context is None:
            return ret
        request = context.get("request", None)
        if request is None:
            return ret
        query_params = request.get("query_params", None)
        if query_params is None:
            return ret
        query_param = query_params.get("expand", None)
        if query_param is None:
            return ret
        field_names = query_param.split(",")
        for field_name in field_names:
            if self.field_name == field_name:
                kw = {"context": self.context}
                if isinstance(self.expand_serializer, str):
                    sc = import_string(self.expand_serializer)
                else:
                    sc = self.expand_serializer
                return sc(obj, **kw).data
        return ret


class LoadableImageField(ImageField):
    """
    An ImageField that can be passed an existing imagefield url, and therefore can be
    used in updates without requiring a file upload.
    """

    def get_field_for_url(self, data):
        model = self.parent.Meta.model
        queryset = model.objects.all()
        for instance in queryset:
            field = getattr(instance, self.field_name, None)
            if field is not None:
                url = getattr(field, "url", None)
                if url is not None:
                    if url in data:
                        return field

    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except ValidationError:
            field = self.get_field_for_url(data)
            return super().to_internal_value(field)


class TimezoneField(Field):
    """
    Serializer field for pytz timezone handling (used with django-timezone-field)

    See:
    https://github.com/mfogel/django-timezone-field/issues/29
    https://github.com/encode/django-rest-framework/pull/3778#issuecomment-167831933
    """

    def to_representation(self, obj):
        return six.text_type(obj)

    def to_internal_value(self, data):
        try:
            return pytz.timezone(str(data))
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValidationError("Unknown timezone")


class ParameterisedHyperlinkedRelatedField(
    ParameterisedFieldMixin, HyperlinkedRelatedField
):

    lookup_fields = [
        #   <model_field>/<url_kwarg>
        #   "user.username"/"username"
        ("pk", "pk")
    ]

    def __init__(self, *args, **kwargs):
        self.lookup_fields = kwargs.pop("lookup_fields", self.lookup_fields)
        super().__init__(*args, **kwargs)


class ParameterisedHyperlinkedIdentityField(HyperlinkedIdentityField):

    # read_only = True
    lookup_fields = [("pk", "pk")]

    def __init__(self, *args, **kwargs):
        self.lookup_fields = kwargs.pop("lookup_fields", self.lookup_fields)
        # self.read_only = kwargs.pop("read_only", self.read_only)
        super().__init__(*args, **kwargs)

    def get_object(self, view_name, view_args, view_kwargs):
        """ Given a URL, return a corresponding object. """
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        lookup_kwargs = {}
        for lookup_field, lookup_url_kwarg in self.lookup_fields:
            if "." in lookup_field:
                lookup_field = lookup_field.replace(".", "__")
            lookup_kwargs[lookup_field] = view_kwargs[lookup_url_kwarg]
        return get_object_or_404(queryset, **lookup_kwargs)

    def get_url(self, obj, view_name, request, format):
        """
        Given an object, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        kwargs = {}
        for model_field, url_param in self.lookup_fields:
            attr = obj
            for field in model_field.split("."):
                attr = getattr(attr, field)
            kwargs[url_param] = attr

        return self.reverse(view_name, kwargs=kwargs, request=request, format=format)


class Base64ImageField(ImageField):
    """
    A Django REST framework field for handling image-uploads through raw post data.
    It uses base64 for encoding and decoding the contents of the file.

    Heavily based on
    https://github.com/tomchristie/django-rest-framework/pull/1268

    Updated for Django REST framework 3.

    see: https://stackoverflow.com/questions/28036404/django-rest-framework-upload-image-the-submitted-data-was-not-a-file
    """

    def to_internal_value(self, data):
        # Check if this is a base64 string
        if isinstance(data, six.string_types):
            # Check if the base64 string is in the "data:" format
            if "data:" in data and ";base64," in data:
                # Break out the header from the base64 content
                header, data = data.split(";base64,")
            # Try to decode the file. Return validation error if it fails.
            try:
                decoded_file = base64.b64decode(data)
            except TypeError:
                self.fail("invalid_image")
            # Generate file name:
            file_name = str(uuid.uuid4())[:12]  # 12 characters are more than enough.
            # Get the file name extension:
            file_extension = self.get_file_extension(file_name, decoded_file)
            complete_file_name = "%s.%s" % (file_name, file_extension)
            data = ContentFile(decoded_file, name=complete_file_name)
        return super().to_internal_value(data)

    def get_file_extension(self, file_name, decoded_file):
        extension = imghdr.what(file_name, decoded_file)
        extension = "jpg" if extension == "jpeg" else extension
        return extension

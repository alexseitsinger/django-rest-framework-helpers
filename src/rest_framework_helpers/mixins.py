"""
https://stackoverflow.com/questions/29362142/django-rest-framework-hyperlinkedidentityfield-with-multiple-lookup-args
http://www.tomchristie.com/rest-framework-2-docs/api-guide/relations
https://github.com/miki725/formslayer/blob/master/formslayer/pdf/relations.py#L7-L46
https://stackoverflow.com/questions/32038643/custom-hyperlinked-url-field-for-more-than-one-lookup-field-in-a-serializer-of-d
https://stackoverflow.com/questions/43964007/django-rest-framework-get-or-create-for-primarykeyrelatedfield
"""
from rest_framework.fields import SkipField
from rest_framework.relations import PKOnlyObject
from collections import OrderedDict
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.http import Http404
from rest_framework.serializers import (
    Field,
    HyperlinkedRelatedField,
    HyperlinkedIdentityField,
    HyperlinkedModelSerializer,
    ImageField,
    ValidationError,
    ListSerializer,
)

from .utils import (
    deep_update,
    get_real_path,
    get_real_field_path,
    get_class_name,
    get_model_field_path,
    remove_redundant_paths,
    get_path_options,
    get_model_path,
    get_mapped_path,
    get_nested_attr,
    has_circular_reference,
    is_model_field,
    assert_no_none,
    has_ancestor,
    HashableList,
    HashableDict,
    # get_nested,
    DictDiffer,
)


class RepresentationMixin(object):
    def to_representation(self, instance, *args, **kwargs):
        ret = OrderedDict()
        fields = self._readable_fields

        for field in fields:
            try:
                obj = field.get_attribute(instance)
            except SkipField:
                continue

            check_for_none = obj.pk if isinstance(obj, PKOnlyObject) else obj
            if check_for_none is None:
                representation = None
            else:
                representation = self.to_representation_for_field(
                    field, obj, *args, **kwargs
                )

            ret[field.field_name] = representation
        return ret

    def to_representation_for_field(self, field, obj, *args, **kwargs):
        return field.to_representation(obj, *args, **kwargs)


class ExplicitFieldsMixin(RepresentationMixin):
    @property
    def explicit_fields(self):
        request = self.context["request"]
        query_params = request.query_params
        fields = query_params.get("fields", "").split(",")
        fields_possible = self.Meta.fields
        fields_chosen = []
        for field_specified in fields:
            if field_specified in fields_possible:
                fields_chosen.append(field_specified)
        return fields_chosen

    def remove_empty_representations(self, ret):
        res = OrderedDict()
        for k, v in ret.items():
            if v is not None:
                res[k] = v
        return res

    def to_representation(self, obj):
        ret = super().to_representation(obj)
        ret = self.remove_empty_representations(ret)
        return ret

    def to_representation_for_field(self, field, obj):
        field_name = field.field_name
        if field_name in self.explicit_fields:
            return field.to_representation(obj)


class DebugOnlyResponseMixin(object):
    """
    Returns the response if in DEBUG mode, otherwise raises a 404.
    """

    def get(self, request, format=None):
        if settings.DEBUG is False:
            return Http404()
        return super().get(request, format)


class EndpointsAllowedMixin(object):
    """
    Only returns endpoints that are allowed.
    """

    endpoints_allowed = []

    def get_endpoints(self, request, format):
        endpoints = super().get_endpoints(request, format)
        allowed = self.endpoints_allowed
        for name, _ in endpoints.items():
            if name not in allowed:
                del endpoints[name]
        return endpoints


class EndpointsRemovedMixin(object):
    """
    Removes the named endpoints from the response.
    """

    endpoints_removed = []

    def get_endpoints(self, request, format):
        endpoints = super().get_endpoints(request, format)
        removed = self.endpoints_removed
        for name, _ in endpoints.items():
            if name in removed:
                del endpoints[name]
        return endpoints


class SkippedFieldsMixin(object):
    """
    Dynamically removes fields from serializer.
    https://stackoverflow.com/questions/27935558/dynamically-exclude-or-include-a-field-in-django-rest-framework-serializer
    """

    def __init__(self, *args, **kwargs):
        skipped_fields = kwargs.pop("skipped_fields", None)
        super().__init__(*args, **kwargs)
        self.remove_skipped_fields(skipped_fields)

    def remove_skipped_fields(self, skipped_fields=None):
        if skipped_fields is not None:
            for field_name in skipped_fields:
                if field_name in self.fields:
                    self.fields.pop(field_name)


class GetOrCreateMixin(object):
    """
    Allows a get or create of an object.
    https://stackoverflow.com/questions/25026034/django-rest-framework-modelserializer-get-or-create-functionality
    """

    def is_valid(self, raise_exception=False):
        if hasattr(self, "initial_data"):
            # if we are instantiating with data={something}.
            try:
                # try to get the object in question.
                obj = self.Meta.model.objects.get(**self.initial_data)
            except (ObjectDoesNotExist, MultipleObjectsReturned):
                # except not find the object or the data being ambigious
                # for defining it. Then validate the data as usual.
                return super().is_valid(raise_exception)
            else:
                # If the object is found, add it to the serializer.
                # Then, validate the data as usual.
                self.instance = obj
                return super().is_valid(raise_exception)
        else:
            # If the serializer was instantiated with just an object,
            # and no data={something} proceed as usual.
            return super().is_valid(raise_exception)


class OrderByFieldNameMixin(object):
    """
    Returns querysets ordered by the field name specified.
    """

    order_by_field_name = None

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.order_by_field_name is not None:
            queryset = queryset.order_by(self.order_by_field_name)
        return queryset


class ExcludeKwargsMixin(object):
    """
    Returns querysets that exclude specified kwargs.
    """

    exclude_kwargs = {}

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.exclude(**self.exclude_kwargs)
        return queryset


class CheckQuerysetObjectPermissionsMixin(object):
    """
    Check object permissions for each object in queryset.
    NOTE: Requires that the permission classes include an object permission check.
    """

    def get_queryset(self):
        queryset = super().get_queryset()
        for obj in queryset:
            self.check_object_permissions(self.request, obj)
        return queryset


class ValidateCurrentUserMixin(object):
    """
    Adds a current_user property to the object.
    """

    @property
    def current_user(self):
        context = getattr(self, "context", None)
        if context is None:
            raise AttributeError("There is no context.")
        request = context.get("request", None)
        if request is None:
            raise KeyError("There is not request in context.")
        user = getattr(request, "user", None)
        if user is None:
            raise AttributeError("There is not user in the request")
        return user

    def validate_with_current_user(self, value):
        if self.current_user != value:
            raise ValidationError(
                "The user specified does not match the current session."
            )


class NestedUserFieldsValidatorsMixin(ValidateCurrentUserMixin):
    """
    Creates a validator for specified fields. Validates the fields value against the
    current user.
    """

    nested_user_fields = {}

    def create_validator_for_nested_user_field(self, bits):
        def validator(value):
            attr = value
            last = value
            for bit in bits:
                last = attr
                attr = getattr(attr, bit, None)
                if attr is None:
                    raise AttributeError(
                        "The attribute '{}' does not exist on object {}.".format(
                            bit, last
                        )
                    )
            self.validate_with_current_user(attr)
            return value

        return validator

    def set_validators_for_nested_user_fields(self):
        for field_name, path in self.nested_user_fields.items():
            validator_name = "validate_{}".format(field_name)
            bits = path.split(".")
            validator = getattr(self, validator_name, None)
            if validator is None:
                validator = self.create_validator_for_nested_user_field(bits)
                setattr(self, validator_name, validator)

    def __init__(self, *args, **kwargs):
        self.set_validators_for_nested_user_fields()
        super().__init__(*args, **kwargs)


class ValidateUserFieldMixin(ValidateCurrentUserMixin):
    """
    Adds a validator for a 'user' field on a serializer.
    """

    def validate_user(self, value):
        self.validate_with_current_user(value)
        return value


class SerializerClassByActionMixin(object):
    """
    Return the serializer class based on the action verb.
    """

    serializer_class_by_action = {}

    def get_serializer_class(self):
        attr = self.serializer_class_by_action
        return attr.get(self.action, super().get_serializer_class())


class PermissionClassesByActionMixin(object):
    """
    Returns a list of permission classes to use based on the action verb.
    https://stackoverflow.com/questions/36001485/django-rest-framework-different-permission-per-methods-within-same-view
    """

    permission_classes_by_action = {}

    def get_permissions(self):
        attr = self.permission_classes_by_action
        for_all = attr.get("all", [])
        for_action = attr.get(self.action, attr.get("default", []))
        permission_classes = for_all + for_action
        if len(permission_classes):
            return [permission_class() for permission_class in permission_classes]
        return super().get_permissions()


class MultipleFieldLookupMixin(object):
    """
    Apply this mixin to any view or viewset to get multiple field filtering based on a
    `lookup_fields` attribute, instead of the default single field filtering.
    """

    def get_object(self):
        queryset = self.get_queryset()  # Get the base queryset
        queryset = self.filter_queryset(queryset)  # Apply any filter backends
        filter = {}
        for field in self.lookup_fields:
            if self.kwargs[field]:  # Ignore empty fields.
                filter[field] = self.kwargs[field]
        return get_object_or_404(queryset, **filter)  # Lookup the object


class HyperlinkListMixin(object):
    """
    List URL attribute from each object.
    """

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            result = [obj["url"] for obj in serializer.data]
            return self.get_paginated_response(result)

        serializer = self.get_serializer(queryset, many=True)
        result = [obj["url"] for obj in serializer.data]
        return Response(result)


class ParameterisedViewMixin(object):
    """
    Used in conjunction with the ParameterisedFieldMixin to enable multiple custom
    lookup_fields for queries.
    """

    lookup_fields = [("pk", "pk")]

    def __init__(self, *args, **kwargs):
        self.lookup_fields = kwargs.pop("lookup_fields", self.lookup_fields)
        super().__init__(*args, **kwargs)

    def get_object_kwargs(self):
        object_kwargs = {}
        for lookup_field, lookup_url_kwarg in self.lookup_fields:
            if "." in lookup_field:
                model_name, field_name = lookup_field.split(".")
                lookup_field = lookup_field.replace(".", "__")
                object_kwargs[lookup_field] = self.kwargs[lookup_url_kwarg]
            else:
                object_kwargs[lookup_field] = self.kwargs[lookup_url_kwarg]
        return object_kwargs

    def get_object(self):
        """
        Filter the queryset to return an object using the parameterised procedure
        instead of the default, so queries can involve more than a single string.
        """
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        object_kwargs = self.get_object_kwargs()
        obj = get_object_or_404(queryset, **object_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj


class ParameterisedFieldMixin(object):
    """
    Used in conjunction with the ParameterisedViewMixin to enable multiple custom
    lookup_fields for serializing.
    """

    lookup_fields = [("pk", "pk")]

    def __init__(self, *args, **kwargs):
        self.lookup_fields = kwargs.pop("lookup_fields", self.lookup_fields)
        super().__init__(*args, **kwargs)

    def use_pk_only_optimization(self):
        """ Return true if all lookup fields for the models is its PK """
        result = False
        for field_tuple in self.lookup_fields:
            if field_tuple[0] and field_tuple[1] == "pk":
                result = True
        return result

    def get_object_kwargs(self, view_kwargs):
        lookup_kwargs = {}
        for lookup_field, lookup_url_kwarg in self.lookup_fields:
            if "." in lookup_field:
                lookup_field = lookup_field.replace(".", "__")
            lookup_kwargs[lookup_field] = view_kwargs[lookup_url_kwarg]
        return lookup_kwargs

    def get_object(self, view_name, view_args, view_kwargs):
        """ Given a URL, return a corresponding object. """
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        lookup_kwargs = self.get_object_kwargs(view_kwargs)
        return get_object_or_404(queryset, **lookup_kwargs)

    def get_url_kwargs(self, obj):
        url_kwargs = {}
        for model_field, url_param in self.lookup_fields:
            attr = obj
            for field in model_field.split("."):
                attr = getattr(attr, field)
            url_kwargs[url_param] = attr
        return url_kwargs

    def get_url(self, obj, view_name, request, format):
        """
        Given an object, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        # # Unsaved objects will not yet have a valid URL.
        if hasattr(obj, "pk") and obj.pk in (None, ""):
            return None
        url_kwargs = self.get_url_kwargs(obj)
        return self.reverse(
            view_name, kwargs=url_kwargs, request=request, format=format
        )


class MeAliasMixin(object):
    def initial(self, request, *args, **kwargs):
        """
        This is the 'dispatch' method for rest_framework.  This has <request.data> etc.

        This augments the request.data to change any values from "me" to
        request.user.username.

        (TODO: Check what the url_kwarg is to determine what part of request.user.<attr>
        to use)

        NOTE: This affects multipart/form-data when we augment its contents and causes
        the formData to be invalid/corrupt.
        """
        if request.user.is_authenticated:
            for k, v in request.data.items():
                if isinstance(v, str):
                    if "/me/" in v:
                        request.data[k] = v.replace(
                            "/me/",
                            "/{}/".format(
                                getattr(request.user, self.me_alias_lookup_field)
                            ),
                        )
                    elif "me" == v:
                        request.data[k] = v.replace(
                            "me", getattr(request.user, self.me_alias_lookup_field)
                        )
        return super().initial(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        # Duplicate and replace the query params
        new_kwargs = dict(**kwargs)
        new_query_params = request.GET.copy()
        if request.user.is_authenticated:
            for k, v in new_query_params.items():
                if v == "me":
                    new_query_params[k] = getattr(
                        request.user, self.me_alias_lookup_field
                    )
            request.GET = new_query_params

            # Duplicate and replace the kwargs
            for k, v in new_kwargs.items():
                if v == "me":
                    k_bits = k.split("__")
                    suffix = k_bits.pop()
                    if suffix:
                        new_kwargs[k] = getattr(request.user, suffix)
                    else:
                        if hasattr(request.user, k):
                            new_kwargs[k] = getattr(request.user, k)
                        else:
                            new_kwargs[k] = request.user

        return super().dispatch(request, *args, **new_kwargs)

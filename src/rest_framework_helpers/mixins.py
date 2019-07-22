"""
https://stackoverflow.com/questions/29362142/django-rest-framework-hyperlinkedidentityfield-with-multiple-lookup-args
http://www.tomchristie.com/rest-framework-2-docs/api-guide/relations
https://github.com/miki725/formslayer/blob/master/formslayer/pdf/relations.py#L7-L46
https://stackoverflow.com/questions/32038643/custom-hyperlinked-url-field-for-more-than-one-lookup-field-in-a-serializer-of-d
https://stackoverflow.com/questions/43964007/django-rest-framework-get-or-create-for-primarykeyrelatedfield
"""
import base64
import six
import uuid
import pytz
import imghdr
import json
import io
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from django.utils.module_loading import import_string
from django.http.request import QueryDict
from django.db import models
from django.db.models import Manager
from django.db.models.query import QuerySet
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, APIClient
from rest_framework.reverse import reverse
from rest_framework.relations import ManyRelatedField
from rest_framework.parsers import JSONParser
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
    get_class_name,
    get_model_field_path,
    get_field_bits,
    get_model_path,
    get_mapped_path,
    get_nested_attr,
    has_circular_reference,
    has_ancestor,
    HashableList,
    HashableDict,
)


class ExpandableMixin(object):
    query_param = "expand"
    settings_attr_name = "expand"
    required_attrs = ["model_name"]
    initialized_attrs = required_attrs + ["target_field_name"]

    def __init__(self, *args, **kwargs):
        for attr_name in self.initialized_attrs:
            attr = getattr(self, attr_name, None)
            if attr is None:
                attr = kwargs.pop(attr_name, None)
            if attr is None and attr_name in self.required_attrs:
                raise AttributeError(
                    "The attribute '{}' is required.".format(attr_name)
                )
            setattr(self, attr_name, attr)
        self.settings = self.get_settings()
        super().__init__(*args, **kwargs)

    def get_settings(self):
        """
        Returns the current settings for expanding.
        """
        settings = getattr(self, "settings", None)
        if settings is not None:
            return settings
        settings_attr_name = "settings_attr_name"
        attr_name = getattr(self, settings_attr_name, None)
        if attr_name is None:
            raise AttributeError("The '{}' is required.".format(settings_attr_name))
        attr = getattr(self, attr_name, None)
        if attr is None:
            raise AttributeError("The '{}' settings are required.".format(attr_name))
        return attr

    def get_request(self, context=None):
        """
        Returns the current request object from the context.
        """
        if context is None:
            context = getattr(self, "context", None)
        if context is None:
            raise AttributeError("Context not found.")
        request = context.get("request", None)
        if request is None:
            raise AttributeError("Request not found in context.")
        return request

    def get_query_param(self, request=None):
        if request is None:
            request = self.get_request()
        query_params = getattr(request, "query_params", None)
        if query_params is None:
            return None
        query_param = query_params.get(self.query_param, None)
        if query_param is None:
            return None
        if not len(query_param):
            return None
        return query_param

    def get_expanded_field_names(self, request=None):
        """
        Returns a list of field names to expand.
        """
        query_param = self.get_query_param()
        return query_param.split(",")

    @property
    def has_query_param(self):
        query_param = self.get_query_param()
        if query_param is None:
            return False
        return True

    def get_representation(self, obj, ancestor_models=[]):
        """
        Fascade method to return the representation.
        """
        if self.has_query_param:
            if any([has_ancestor(obj, x) is True for x in ancestor_models]):
                return self.to_default_representation(obj)
            return self.to_expanded_representation(obj)
        else:
            return self.to_default_representation(obj)

    def to_default_representation(self, obj):
        """
        Method for converting the object to its default representation.
        """
        return super().to_representation(obj)

    def to_expanded_representation(self, obj):
        """
        Method for converting the object to an expanded representation.
        """
        field_names = self.get_expanded_field_names()
        expanded = self.get_expanded_representation(obj, field_names)
        if expanded is None:
            return self.to_default_representation(obj)
        if isinstance(expanded, list):
            return HashableList(expanded)
        return HashableDict(expanded)

    def get_expanded_object(
        self,
        obj,
        field_name=None,
        parent=None,
        field_options=None,
        expand_options=None,
        ignored_fields=[],
    ):
        opts = [field_options, expand_options]

        if field_name is None:
            if any([x is None for x in opts]):
                raise RuntimeError(
                    "The expand and field options cannot be empty with no field name."
                )

        prefix = None
        suffix = None

        if field_name is not None:
            prefix, suffix = field_name.rsplit(".", 1)

            if all([x is None for x in opts]):
                attr = getattr(obj, suffix, None)
                if attr is not None and isinstance(attr, Manager):
                    field_options = self.get_field_options(prefix, parent)
                    expand_options = self.get_expand_options(obj, prefix)
                else:
                    field_options = self.get_field_options(field_name, parent)
                    expand_options = self.get_expand_options(obj, field_name)

        expanded = self.expand_object(obj, field_options, expand_options)

        if all([x is not None for x in [prefix, suffix]]):
            nested_path = get_model_field_path(prefix, suffix)
            exopts = self.get_expand_options(obj, nested_path)
            fopts = self.get_field_options(nested_path, parent=obj)
            field = exopts["field"]
            if field == obj:
                print("Same object!")
            elif has_circular_reference(field) is True:
                print("Circular reference!")
            else:
                nested_obj = self.get_expanded_object(
                    field,
                    field_name=nested_path,
                    parent=obj,
                    field_options=fopts,
                    expand_options=exopts,
                )
                expanded[suffix] = nested_obj
        return expanded

    def get_expanded_representation(self, obj, field_names, parent=None):
        for field_name in field_names:
            full_name = get_model_field_path(self.model_name, field_name)
            for item in self.settings:
                if full_name in item.get("fields", []):
                    return self.get_expanded_object(
                        obj, full_name, parent, ignored_fields=["userprofile"]
                    )

    def expand_object(self, obj, field_options, expand_options):
        context = self.context
        serializer = field_options["serializer"]
        many = field_options["many"]
        serializer_class = self.get_serializer_class(serializer)
        class_name = get_class_name(self)
        try:
            instance = serializer_class(
                context=context,
                many=many,
                skipped_fields=field_options["skipped_fields"],
            )
            # if many is True and not isinstance(obj, QuerySet):
            # obj = QuerySet(obj)
            rep = instance.to_representation(obj)
            return rep
        except AttributeError as exc:
            msg = str(exc)
            if msg.startswith("'ManyRelatedManager' object has no attribute"):
                raise AttributeError(
                    "{class_name}'s expandable attr is missing: 'many': True".format(
                        class_name=class_name
                    )
                )
            raise exc

    def get_expand_options(self, obj, full_path=""):
        field, valid_bits, skipped_bits, ignored_bits, mapping = get_field_bits(
            obj, full_path
        )
        mapped_path = get_mapped_path(mapping)
        return {
            "field": field,
            "path": mapped_path,
            "bits": {
                "valid": valid_bits,
                "skipped": skipped_bits,
                "ignored": ignored_bits,
            },
        }

    def get_field_options(self, field_name, parent):
        """
        Returns a dictionary of kwargs to use for expanding the specified field or
        raises an exception.
        """
        matched = False
        ret = {
            "serializer": "path.to.serializer.class.SerializerClass",
            "many": False,
            "skipped_fields": [],
        }

        for item in self.settings:
            if field_name in item.get("fields", []):
                matched = True
                ret["serializer"] = item.get("serializer", ret["serializer"])
                ret["many"] = item.get("many", ret["many"])
                ret["skipped_fields"] = item.get(
                    "skipped_fields", ret["skipped_fields"]
                )

        if matched is False:
            raise AttributeError(
                "There is no specification for '{field_name}' in {class_name}RelatedField.\n\n"
                "Add a dictionary to the 'expandable' list with:\n"
                "    'serializer': '{serializer_path}'\n"
                "    'fields': ['{field_name}']\n"
                "    'many': {many}".format(
                    field_name=field_name,
                    class_name=get_class_name(parent),
                    serializer_path=ret["serializer"],
                    many=ret["many"],
                )
            )

        return ret

    def get_serializer_class(self, serializer_path):
        """
        Returns the serializer class to use for serializing the object instances.
        """
        target = None

        for item in self.settings:
            if serializer_path == item["serializer"]:
                target = item

        if target is None:
            raise AttributeError(
                "Failed to find an entry for serializer '{}'.".format(serializer_path)
            )

        klass = target.get("serializer_class", None)
        if klass is None:
            klass = target["serializer_class"] = import_string(serializer_path)

        return klass


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
    def is_valid(self, raise_exception=False):
        #
        # Allows us to get_or_create an object.
        #
        # https://stackoverflow.com/questions/25026034/django-rest-framework-modelserializer-get-or-create-functionality
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
    order_by_field_name = None

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.order_by_field_name is not None:
            queryset = queryset.order_by(self.order_by_field_name)
        return queryset


class ExcludeKwargsMixin(object):
    exclude_kwargs = {}

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.exclude(**self.exclude_kwargs)
        return queryset


class IsObjectUserQuerysetMixin(object):
    """
    Check object permissions for each object in queryset.
    NOTE: Requires that the permission classes include an object permission check. ie: IsObjectUser
    """

    def get_queryset(self):
        queryset = super().get_queryset()
        for obj in queryset:
            self.check_object_permissions(self.request, obj)
        return queryset


class NestedUserFieldsValidatorsMixin(object):
    """
    Creates a validator for a fields dynamically. Validates the nested fields value against the current user.
    """

    nested_user_fields = {}

    def set_nested_user_fields_validators(self):
        # create the path to get from the value
        # path = self.nested_user_field
        for field_name, path in self.nested_user_fields.items():
            validator_name = "validate_{}".format(field_name)
            bits = path.split(".")

            # create a method for the validator
            def validator(value):
                attr = value
                for name in bits:
                    attr = getattr(attr, name)
                if self.context["request"].user != attr:
                    raise ValidationError("User must match the current session")
                return value

            # dynamically set the validator method
            setattr(self, validator_name, validator)

    def __init__(self, *args, **kwargs):
        self.set_nested_user_fields_validators()
        super().__init__(*args, **kwargs)


class ValidateUserMixin(object):
    def validate_user(self, value):
        if self.context["request"].user != value:
            raise ValidationError("User must match the current session")
        return value


class ValidateFieldForCurrentUserMixin(object):
    validate_field_for_current_user = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_validator_for_field()

    def add_validator_for_field(self):
        def validator(value):
            if self.context["request"].user != value:
                raise ValidationError("User must match the current sesssion")
            return value

        validator_name = "validate_{}".format(self.validate_field_for_current_user)
        setattr(self, validator_name, validator)


class SerializerClassByActionMixin(object):
    """ Return the serializer class based on the action verb. """

    def get_serializer_class(self):
        try:
            return self.serializer_class_by_action[self.action]
        except KeyError:
            return self.serializer_class_by_action["default"]


class QuerysetObjectPermissionsMixin(object):
    """
        A mixin class to force checking object permissions for each object in queryset.
    """

    def get_queryset(self):
        queryset = super().get_queryset()
        for obj in queryset:
            self.check_object_permissions(self.request, obj)
        return queryset


class PermissionClassesByActionMixin(object):
    """
    https://stackoverflow.com/questions/36001485/django-rest-framework-different-permission-per-methods-within-same-view
    """

    def get_permissions(self):
        try:
            # return permission_classes depending on `action`
            return [
                permission()
                for permission in self.permission_classes_by_action[self.action]
            ]
        except KeyError:
            # action is not set return default permission_classes
            return [
                permission()
                for permission in self.permission_classes_by_action["default"]
            ]


class AlphabeticalOrderQuerysetMixin(object):

    # the field to aphabetize things by.
    # defaults to "name"
    alphabetical_order_field = "name"

    def get_queryset(self):
        queryset = super(AlphabeticalOrderQuerysetMixin, self).get_queryset()
        # queryset = self.filter_queryset(queryset)
        queryset = queryset.order_by(self.alphabetical_order_field)
        return queryset


class MultipleFieldLookupMixin(object):
    """
    Apply this mixin to any view or viewset to get multiple field filtering
    based on a `lookup_fields` attribute, instead of the default single field filtering.
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
    """ List URL attribute from each object. """

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
        Used in conjunction with the ParameterisedFieldMixin to enable multiple custom lookup_fields for queries.
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
        Filter the queryset to return an object using the parameterised procedure instead of the default, so queries can involve more than a single string.
        """
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        object_kwargs = self.get_object_kwargs()
        obj = get_object_or_404(queryset, **object_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj


class ParameterisedFieldMixin(object):
    """
        Used in conjunction with the ParameterisedViewMixin to enable multiple custom lookup_fields for serializing.
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
        This is the 'dispatch' method for rest_framework.
        This has <request.data> etc.

        This augments the request.data to change any values from "me" to request.user.username.

        (TODO: Check what the url_kwarg is to determine what part of request.user.<attr> to use)

        NOTE:
        This affects multipart/form-data when we augment its contents and causes the formData to be invalid/corrupt.
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

"""
    https://stackoverflow.com/questions/29362142/django-rest-framework-hyperlinkedidentityfield-with-multiple-lookup-args

    http://www.tomchristie.com/rest-framework-2-docs/api-guide/relations
    https://github.com/miki725/formslayer/blob/master/formslayer/pdf/relations.py#L7-L46

    https://stackoverflow.com/questions/32038643/custom-hyperlinked-url-field-for-more-than-one-lookup-field-in-a-serializer-of-d

    https://stackoverflow.com/questions/43964007/django-rest-framework-get-or-create-for-primarykeyrelatedfield
"""
from django.core.exceptions import (
    ObjectDoesNotExist,
    MultipleObjectsReturned,
)
from django.shortcuts import get_object_or_404
from rest_framework.serializers import ValidationError


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
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes_by_action["default"]]


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
        queryset = self.get_queryset()             # Get the base queryset
        queryset = self.filter_queryset(queryset)  # Apply any filter backends
        filter = {}
        for field in self.lookup_fields:
            if self.kwargs[field]: # Ignore empty fields.
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
        result = [obj['url'] for obj in serializer.data]
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
            if field_tuple[0] and field_tuple[1] == 'pk':
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
            for field in model_field.split('.'):
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
        if hasattr(obj, 'pk') and obj.pk in (None, ''):
            return None
        url_kwargs = self.get_url_kwargs(obj)
        return self.reverse(view_name, kwargs=url_kwargs, request=request, format=format)


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
                        request.data[k] = v.replace("/me/", "/{}/".format(
                            getattr(request.user, self.me_alias_lookup_field),
                        ))
                    elif "me" == v:
                        request.data[k] = v.replace("me", getattr(request.user, self.me_alias_lookup_field))
        return super().initial(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        # Duplicate and replace the query params
        new_kwargs = dict(**kwargs)
        new_query_params = request.GET.copy()
        if request.user.is_authenticated:
            for k,v in new_query_params.items():
                if v == "me":
                    new_query_params[k] = getattr(request.user, self.me_alias_lookup_field)
            request.GET = new_query_params

            # Duplicate and replace the kwargs
            for k,v in new_kwargs.items():
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

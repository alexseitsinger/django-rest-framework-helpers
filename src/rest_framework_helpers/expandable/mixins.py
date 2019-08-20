from rest_framework.relations import ManyRelatedField
from django.db.models import Manager
from django.db.models.query import QuerySet
from django.utils.module_loading import import_string

from ..utils import (
    get_object,
    get_class_name,
    remove_redundant_paths,
    get_model_field_path,
    get_path_parts,
    DictDiffer,
    HashableList,
    HashableDict,
)
from ..mixins import RepresentationMixin


# TODO: Add an assertion for field names existing on the model.
# TODO: Detect and fallback to default representation for circular references instead of
# just removing the field completely on the parent.


class ExpandableMixin(object):
    model_name = None
    query_param = "expand"

    @property
    def class_name(self):
        """
        Returns the name of the current class.
        """
        return get_class_name(self)

    @property
    def request(self):
        """
        Returns the current request context passed from DRF.
        """
        context = getattr(self, "context", None)
        if context is None:
            raise AttributeError("Context not found.")
        request = context.get("request", None)
        if request is None:
            raise AttributeError("Request not found in context.")
        return request

    @property
    def params(self):
        """
        Returns a list of unique relative field paths that should be used for expanding.
        """
        attr_name = getattr(self, "query_param", None)

        if attr_name is not None:
            query_params = getattr(self.request, "query_params", {})
            result = query_params.get(attr_name, "").split(",")
            result = list(set(result))
            result = remove_redundant_paths(result)
            result = [x for x in result if len(x)]
            return result

    @property
    def has_param(self):
        """
        Returns True/False if the expand query param was used, and it has value(s). This
        will return False is an empty expand= query param is used.
        """
        if self.params is None:
            return False
        return True

    def get_model_name(self):
        """
        Returns the model name from the ModelSerializer Meta class model specified, or
        from the previously saved model name on the class.
        """
        model_name = getattr(self, "model_name", None)
        if model_name is None:
            model = self.Meta.model
            model_name = model.__name__.lower()
            self.model_name = model_name
        return model_name

    def get_field_path(self, path):
        """
        Returns a list of possible field paths that are prefixed with the current
        serializers model name, plus one suffixed with _set for django's default
        reverse relationship names.
        """
        model_name = self.get_model_name()
        prefix = "{}.".format(model_name)
        if not path.startswith(prefix):
            return get_model_field_path(model_name, path)
        return path

    def is_requested(self, field_name):
        field_path = self.get_field_path(field_name)
        if field_path in self.requested_field:
            return True
        return False

    @property
    def requested_fields(self):
        """
        Returns a list of field paths that are requested via the query param. These
        are used to specify the fields to expand.
        """
        return [self.get_field_path(x) for x in self.params]


class ExpandableModelSerializerMixin(RepresentationMixin, ExpandableMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initialize_expandable_fields()

    def initialize_expandable_fields(self):
        model_name = self.get_model_name()

        for field_name, field in self.expandable_fields:
            # Add references to the parent model serializer and field name used.
            field.model_serializer = self
            field.model_serializer_field_name = field_name
            # Set the model name.
            field.model_name = model_name
            # Set the allowed paths.
            field.allowed_prefix = "{}.{}".format(model_name, field_name)
            field.allowed = list(set([field_name] + getattr(field, "allowed", [])))

    @property
    def expandable_fields(self):
        """
        Returns a list of all the fields that subclass ExpandableRelatedFieldMixin
        """
        fields = []

        for field_name, field in self.fields.items():
            target = (
                field.child_relation if isinstance(field, ManyRelatedField) else field
            )

            if isinstance(target, ExpandableRelatedFieldMixin):
                fields.append([field_name, target])

        return fields

    def is_expandable(self, field):
        """
        Returns True if the field is a subclass of the ExpandableRelatedFieldMixin
        """
        target = field.child_relation if isinstance(field, ManyRelatedField) else field

        for field_name, field in self.expandable_fields:
            if field == target:
                return True

        return False

    def get_matched_paths(self, expandable_field):
        matched = []

        for requested_path in self.requested_fields:
            if expandable_field.is_matching(requested_path):
                expandable_field.assert_is_allowed(requested_path)
                expandable_field.assert_is_specified(requested_path)
                matched.append(requested_path)

        return matched

    def to_representation_for_field(self, field, obj):
        """
        A function to customize what each field representation produces. Can be
        overwritten in sublclasses to add custom behavoir on a per-field basis.

        By default, if the field is an expandable field, it will check if it should be
        expanded, and do so if checks pass.
        """
        if isinstance(obj, Manager):
            obj = obj.all()

        if self.is_expandable(field):
            target = getattr(field, "child_relation", field)
            matched = self.get_matched_paths(target)
            if len(matched):
                return target.to_expanded_representation(obj, matched)
        return field.to_representation(obj)


class ExpandableRelatedFieldMixin(ExpandableMixin):
    settings_attr = "expand_settings"
    initialized_attrs = ["allowed", "ignored"]
    comparison_field_name = "uuid"

    def __init__(self, *args, **kwargs):
        for name in self.initialized_attrs:
            kwarg = kwargs.pop(name, None)
            if kwarg is not None:
                setattr(self, name, kwarg)

        super().__init__(*args, **kwargs)

    @property
    def settings(self):
        """
        Returns the settings used for this related field instance.
        """
        return getattr(self, self.settings_attr, {})

    @property
    def ignored_paths(self):
        """
        Returns a list of field paths to ignore when generating the representation of
        this field instance.
        """
        ignored_paths = []
        ignored = getattr(self, "ignored", None)

        if ignored is not None:
            for path in ignored:
                ignored_paths.append(self.get_field_path(path))

        return ignored_paths

    def is_ignored(self, path):
        """
        Returns True/False if the specified path is one of the ignored field paths. Used
        by to_representation_for_field to determine if the field is the one to expand.
        """
        if path in self.ignored_paths:
            return True

        return False

    def to_non_circular_path(self, path):
        if self.is_circular(path):
            try:
                prefix, field_name = path.rsplit(".", 1)
                return prefix
            except ValueError:
                return path
        return path

    def is_circular(self, path):
        try:
            prefix, field_name = path.rsplit(".", 1)
        except ValueError:
            field_name = path

        if field_name in self.circular_field_names:
            return True
        return False

    @property
    def circular_field_names(self):
        circular_field_names = []

        # Remove circular references to the parent model.
        parent_model_name = self.model_serializer.get_model_name()
        parent_set_name = "{}_set".format(parent_model_name)
        parent_names = (parent_model_name, parent_set_name)
        for parent_name in parent_names:
            circular_field_names.append(parent_name)

        return circular_field_names

    def get_skipped_fields(self, skipped=None):
        """
        Returns a list of field paths (ignored and skipped) to pass to the serializer
        class so it doensn't return them in the representation.
        """
        skipped_fields = self.ignored_paths

        for field_name in self.circular_field_names:
            skipped_fields.append(field_name)

        if skipped is not None:
            skipped_fields.extend(skipped)

        return list(set(skipped_fields))

    @property
    def allowed_paths(self):
        """
        Returns a list of field paths that are permitted to be expanded from this
        expandable class instance.
        """
        allowed_paths = []
        allowed = getattr(self, "allowed", None)
        if allowed is not None:
            for path in allowed:
                allowed_paths.append(self.get_field_path(path))
        return allowed_paths

    def is_allowed(self, path):
        """
        Returns True/False if the specified path is one of the allowed field paths. Used
        by to_representation_for_field to determine if the field is to be expanded.
        """
        if path.startswith(self.allowed_prefix):
            return True
        if path in self.allowed_paths:
            return True
        return False

    def assert_is_allowed(self, path):
        """
        Raises an AssertionError if the field path specified is not in the list of
        allowed field paths.
        """
        model_serializer_name = get_class_name(self.model_serializer)
        model_serializer_field_name = self.model_serializer_field_name
        related_field_class_name = get_class_name(self)
        if self.is_allowed(path) is False:

            path = ".".join(path.split(".")[1:])

            raise AssertionError(
                "The path '{}' is not listed as an allowed field path on {}'s {} "
                "field. Please add the path to 'allowed' kwarg on {}'s '{}' field "
                "to allow its expansion.".format(
                    path,
                    model_serializer_name,
                    model_serializer_field_name,
                    model_serializer_name,
                    model_serializer_field_name,
                )
            )

    def assert_is_specified(self, path):
        """
        Raises an AssertionError if the field path specified is not in the list of
        entries in the 'expands' attribute on the related field class instance.
        """
        if self.is_specified(path) is False:
            # if field_path.startswith(self.model_name):
            #    field_path.replace("{}.".format(self.model_name), "")
            msg = []
            indent = "\n"
            for d in self.settings.get("serializers", []):
                msg.append(
                    "{}{}{}".format(d["serializer"], indent, indent.join(d["paths"]))
                )

            raise AssertionError(
                "The field path '{field_path}' is not specified in '{attr_name}' on "
                "{related_field_class_name}.\n\nCurrently Specified:\n{specified}".format(
                    field_path=path,
                    attr_name=self.settings_attr,
                    related_field_class_name=self.class_name,
                    specified="\n".join(msg),
                )
            )

    def is_specified(self, path):
        """
        Returns True/False if the specified path is in any of the listed paths  on the
        class isntance's 'expands' attribute.
        """
        for d in self.settings.get("serializers", []):
            if path in d.get("paths", []):
                return True
        return False

    def is_matching(self, requested_path):
        base_path = self.get_field_path(self.model_serializer_field_name)
        is_starting = requested_path.startswith(base_path)
        if is_starting:
            return True
        return False

    def to_default_representation(self, obj):
        """
        Returns the default representation of the object.
        """
        return super().to_representation(obj)

    def expand_object(self, obj, path):
        """
        Method for expanding a model instance object. If a target field name is
        specified, the serializer will use that nested object to generate a
        representation.
        """
        # If the field exists, but its an empty object (no entry saved), obj will be
        # None. So, if we get None as obj, return None instead of trying to serializer
        # its representation.
        if obj is None:
            return None

        serializer = self.get_serializer(obj, path)
        representation = serializer.to_representation(obj)

        return representation

    def get_alias(self, prefix_field, prefix_path, suffix_field, suffix_path):
        for d in self.settings.get("aliases", []):
            if prefix_path in d.get("paths", []):
                alias = d.get("alias", {})
                prefix_field = alias.get("prefix_field", prefix_field)
                prefix_path = alias.get("prefix_path", prefix_path)
                suffix_field = alias.get("suffix_field", suffix_field)
                suffix_path = alias.get("suffix_path", suffix_path)
        return (prefix_field, prefix_path, suffix_field, suffix_path)

    def expand(self, obj, prefix_field, prefix_path, suffix_field, suffix_path):
        if isinstance(obj, Manager):
            obj = obj.all()

        target = obj
        target_name = get_class_name(get_object(target)).lower()
        names = (target_name, "{}_set".format(target_name))

        if len(prefix_field) and prefix_field not in names:
            target = getattr(target, prefix_field, target)

        expanded = self.expand_object(target, prefix_path)

        if len(suffix_field):
            expanded[suffix_field] = self.get_expanded(target, suffix_path)

        return expanded

    def get_expanded(self, obj, path):
        """
        Fascade method for expanding objects or querysets into expanded (nested)
        representations.
        """
        prefix_field, prefix_path, suffix_field, suffix_path = get_path_parts(obj, path)
        prefix_field, prefix_path, suffix_field, suffix_path = self.get_alias(
            prefix_field, prefix_path, suffix_field, suffix_path
        )
        if isinstance(obj, QuerySet):
            return [self.get_expanded(o, path) for o in obj]

        return self.expand(obj, prefix_field, prefix_path, suffix_field, suffix_path)

    def to_expanded_representation(self, obj, paths):
        """
        Entry method for converting an model object instance into a representation by
        expanding the paths specified (if they are allowed and specified).
        """
        if isinstance(obj, Manager):
            obj = obj.all()

        expanded = None

        if len(paths) > 1:
            for path in paths:
                prefix, suffix = path.rsplit(".", 1)
                # base_name = prefix.split(".")[0]

                item = self.get_expanded(obj, path)

                if expanded is None:
                    expanded = item

                elif isinstance(expanded, list):
                    for d1 in expanded:
                        if isinstance(item, list):
                            for d2 in item:
                                field_name = self.comparison_field_name
                                if d2[field_name] == d1[field_name]:
                                    diff = DictDiffer(d2, d1)
                                    changed = diff.changed()
                                    if suffix in changed:
                                        d1.update({suffix: d2[suffix]})

                else:
                    diff = DictDiffer(item, expanded)
                    changed = diff.changed()
                    if suffix in changed:
                        expanded.update({suffix: item[suffix]})
        else:
            path = paths[0]
            # base_name = path.split(".")[0]
            expanded = self.get_expanded(obj, path)

        if isinstance(expanded, list):
            return HashableList(expanded)
        return HashableDict(expanded)

    def get_serializer(self, source, path=None):
        """
        Finds and returns the serializer class instance to use. Either imports the class
        specified in the entry on the 'expands' attribute of the ExpandableRelatedField
        instance, or re-uses the serializer class that was already imported and saved to
        the settings previously.
        """
        serializer_class = None
        ret = {"skipped_fields": [], "many": False, "context": self.context}

        if isinstance(source, Manager):
            source = source.all()

        if isinstance(source, (ManyRelatedField, QuerySet)):
            ret["many"] = True

        for d in self.settings.get("serializers", []):
            if path in d.get("paths", []):
                serializer_class = self.get_serializer_class(d["serializer"])
                ret["skipped_fields"] = self.get_skipped_fields(d.get("skipped", []))
                ret["many"] = d.get("many", ret["many"])

        if not isinstance(source, QuerySet):
            ret["many"] = False
        # if ret["many"] is True:
        #    if not isinstance(source, (QuerySet)):
        #        source = QuerySet(source)

        if serializer_class is None:
            raise RuntimeError(
                "There is no specification for '{path}' in {class_name}.\n\n"
                "Add a dictionary to the 'expandable' list with:\n"
                "    'paths': ['{path}']".format(path=path, class_name=self.class_name)
            )

        # print("---------- get_serializer_class -----------")
        # print("path: ", path)
        # print("serializer_class: ", serializer_class.__name__)
        return serializer_class(**ret)

    def get_serializer_class(self, serializer_path):
        """
        Returns the serializer class to use for serializing the object instances.
        """
        target = None

        for d in self.settings.get("serializers", []):
            if serializer_path == d.get("serializer", ""):
                target = d

        if target is None:
            raise AttributeError(
                "Failed to find an entry for serializer '{}'.".format(serializer_path)
            )

        klass = target.get("serializer_class", None)
        if klass is None:
            klass = target["serializer_class"] = import_string(serializer_path)

        return klass

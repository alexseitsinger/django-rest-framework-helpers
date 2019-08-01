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

    def get_path_parts(self, path):
        """
        Returns a list of possible field paths that are prefixed with the current
        serializers model name, plus one suffixed with _set for django's default
        reverse relationship names.
        """
        model_name = self.get_model_name()
        if not path.startswith(model_name):
            return get_model_field_path(model_name, path)
        return path

    def is_requested(self, field_name):
        field_path = self.get_path_parts(field_name)
        for requested_field in self.requested_fields:
            if requested_field == field_path:
                return True
        return False

    @property
    def requested_fields(self):
        """
        Returns a list of field paths that are requested via the query param. These
        are used to specify the fields to expand.
        """
        return [self.get_path_parts(x) for x in self.params]


class ExpandableModelSerializerMixin(RepresentationMixin, ExpandableMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        model_name = self.get_model_name()

        for field_name, field in self.expandable_fields:
            field.model_serializer = self
            field.model_serializer_field_name = field_name
            field.model_name = model_name
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

    def get_matched_paths(self, target):
        matched = []

        for requested_field in self.requested_fields:
            if target.is_matching(requested_field):
                target.assert_is_allowed(requested_field)
                target.assert_is_specified(requested_field)
                print("  -> requested_field: ", requested_field)
                print("  -> field: ", target)
                # is_allowed = target.is_allowed(requested_field)
                # is_specified = target.is_specified(requested_field)
                # print("  -> allowed ({}): {}".format(requested_field, is_allowed))
                # print("  -> specified ({}): {}".format(requested_field, is_specified))

                # if is_allowed and is_specified:
                matched.append(requested_field)

        return matched

    def to_representation_for_field(self, field, obj):
        """
        A function to customize what each field representation produces. Can be
        overwritten in sublclasses to add custom behavoir on a per-field basis.

        By default, if the field is an expandable field, it will check if it should be
        expanded, and do so if checks pass.
        """
        print("---------- to_representation_for_field ----------")
        print("class: ", self.class_name)
        print("field: ", field.field_name)

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
                ignored_paths.append(self.get_path_parts(path))

        return ignored_paths

    def is_ignored(self, path):
        """
        Returns True/False if the specified path is one of the ignored field paths. Used
        by to_representation_for_field to determine if the field is the one to expand.
        """
        if path in self.ignored_paths:
            return True

        return False

    def get_removed_fields(self, skipped_fields=None):
        """
        Returns a list of field paths (ignored and skipped) to pass to the serializer
        class so it doensn't return them in the representation.
        """
        removed_fields = self.ignored_paths

        if skipped_fields is not None:
            removed_fields.extend(skipped_fields)

        return list(set(removed_fields))

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
                allowed_paths.append(self.get_path_parts(path))
        return allowed_paths

    def is_allowed(self, path):
        """
        Returns True/False if the specified path is one of the allowed field paths. Used
        by to_representation_for_field to determine if the field is to be expanded.
        """
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
            indent = "\n        "
            for d in self.settings.get("serializers", []):
                msg.append(
                    "{}{}{}".format(d["serializer"], indent, indent.join(d["paths"]))
                )

            raise AssertionError(
                "The path '{}' is not listed in the 'expand' attribute on the {} "
                "class used for {} on {}. Please add an entry to the expandable "
                "related field class with the correct serializer to use for the path to "
                "make it expandable.\n\nCurrently specified on {}:\n    {}".format(
                    path,
                    self.class_name,
                    self.model_serializer_field_name,
                    get_class_name(self.model_serializer),
                    self.class_name,
                    "\n    ".join(msg),
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
        field_path_base = self.get_path_parts(self.model_serializer_field_name)
        if requested_path.startswith(field_path_base):
            return True
        return False

    def to_default_representation(self, obj):
        """
        Returns the default representation of the object.
        """
        return super().to_representation(obj)

    def expand_object(self, obj, path, field_name=None):
        """
        Method for expanding a model instance object. If a target field name is
        specified, the serializer will use that nested object to generate a
        representation.
        """
        target = obj
        if field_name is not None:
            if hasattr(target, field_name):
                target = getattr(target, field_name)

        if not target:
            return None

        serializer = self.get_serializer(target, path)
        representation = serializer.to_representation(target)

        return representation

    def get_alias(self, path):
        for d in self.settings.get("aliases", []):
            if path in d.get("paths", []):
                base_name = d.get("base_name", None)
                alias = d.get("alias", "")
                return base_name, alias
        return None, path

    def get_expanded(self, obj, path, base_name=None):
        """
        Fascade method for expanding objects or querysets into expanded (nested)
        representations.
        """
        print("---------- get_expanded() ----------")

        print("path: ", path)

        # base_name, path = self.replace_alias(path)

        if base_name is None:
            # base_name = get_class_name(get_object(obj)).lower()
            base_name = self.get_model_name()

        print(" -> obj: ", obj)
        print(" -> path: ", path)
        print(" -> base name: ", base_name)

        prefix_field, prefix_path, suffix_field, suffix_path = get_path_parts(
            obj, path, base_name
        )
        base_name, prefix_path = self.get_alias(prefix_path)
        base_name, suffix_path = self.get_alias(suffix_path)

        print(" -> prefix_field: ", prefix_field)
        print(" -> prefix_path: ", prefix_path)
        print(" -> suffix_field: ", suffix_field)
        print(" -> suffix_path: ", suffix_path)

        if isinstance(obj, QuerySet):
            print("expand queryset")
            expanded = []

            for o in obj:
                print("expand queryset (prefix)")
                expanded_object = self.expand_object(o, prefix_path, prefix_field)

                if len(suffix_field):
                    print("expand queryset (suffix)")
                    expanded_object[suffix_field] = self.get_expanded(
                        o, suffix_path, base_name
                    )

                expanded.append(expanded_object)
        else:
            # base_name = get_class_name(get_object(obj)).lower()

            print("expand object (prefix)")
            try:
                expanded = self.expand_object(obj, prefix_path, prefix_field)
            except AttributeError:
                expanded = self.expand_object(obj, prefix_path)

            if len(suffix_field):
                print("expand object (suffix)")
                # if suffix_field == "userprofile":
                #    o = getattr(obj, "userprofile")
                expanded[suffix_field] = self.get_expanded(obj, suffix_path, base_name)

        # except AttributeError:
        #     print("expand object (exception)")
        #     expanded = self.expand_object(obj, prefix_path)

        return expanded

    def to_expanded_representation(self, obj, paths):
        """
        Entry method for converting an model object instance into a representation by
        expanding the paths specified (if they are allowed and specified).
        """
        print("---------- to_expanded_representation ----------")
        if isinstance(obj, Manager):
            obj = obj.all()

        expanded = None
        if len(paths) > 1:
            for path in paths:
                prefix, suffix = path.rsplit(".", 1)

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
            expanded = self.get_expanded(obj, paths[0])

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
                ret["skipped_fields"] = self.get_removed_fields(d.get("skipped", []))
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

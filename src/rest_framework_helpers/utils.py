from django.db.models.fields.related import (
    ManyToOneRel,
    ForeignObjectRel,
    OneToOneRel,
    ManyToManyField,
    ForeignKey,
    OneToOneField,
)
from django.db.models import Manager
from collections import OrderedDict

REVERSE_RELS = (ManyToOneRel, OneToOneRel, ForeignObjectRel)
RELS = (ManyToManyField, ForeignKey, OneToOneField)
ACTION_MAPS = {
    "list_route": {"get": "list", "post": "create"},
    "detail_route": {
        "get": "retrieve",
        "put": "update",
        "patch": "partial_update",
        "delete": "destroy",
    },
}


def is_rel(obj):
    name = obj.__class__.__name__
    names = [x.__class__.__name__ for x in RELS]
    if name in names:
        return True
    return False


def is_reverse_rel(obj):
    name = obj.__class__.__name__
    names = [x.__class__.__name__ for x in REVERSE_RELS]
    if name in names:
        return True
    return False


def get_reverse_rels(obj):
    if is_rel(obj) or is_reverse_rel(obj) or isinstance(obj, Manager):
        obj = obj.model
    fields = obj._meta.get_fields()
    return [x for x in fields if is_reverse_rel(x)]


def get_model_path(obj):
    if is_rel(obj) or is_reverse_rel(obj) or isinstance(obj, Manager):
        obj = obj.model
    meta = obj._meta
    path = "{}.{}".format(meta.app_label, meta.model_name)
    path = path.lower()
    return path


def has_model_path(obj, model_path):
    model_path = model_path.lower()
    if is_rel(obj) or is_reverse_rel(obj) or isinstance(obj, Manager):
        obj = obj.model
    path = get_model_path(obj)
    if path == model_path:
        return True
    return False


def get_rels(obj):
    if is_rel(obj) or is_reverse_rel(obj) or isinstance(obj, Manager):
        obj = obj.model
    fields = obj._meta.get_fields()
    return [x for x in fields if is_rel(x)]


def has_circular_reference(obj):
    result = False
    for rel in get_rels(obj):
        if result is True:
            continue
        mp = get_model_path(rel)
        result = has_ancestor(obj, mp)
    return result


def has_ancestor(obj, model_path, checked=[]):
    result = False

    mp = get_model_path(obj)
    if mp not in checked:
        checked.append(mp)
        result = has_model_path(obj, model_path)

    for field in get_reverse_rels(obj):
        if result is True:
            continue

        mp = get_model_path(field)
        if mp not in checked:
            checked.append(mp)
            result = has_model_path(field, model_path)

        if result is False:
            result = has_ancestor(field, model_path, checked)

    return result


def get_class_name(obj=None):
    # Get name of parent object.
    if obj is None:
        return "Unnamed"
    else:
        return obj.__class__.__name__


def get_model_field_path(model_name, *args):
    final_args = []
    if model_name.startswith("."):
        model_name = model_name[1:]
    if model_name.endswith("."):
        model_name = model_name[:-1]
    for arg in list(args):
        if arg is None:
            continue
        if arg.startswith("."):
            arg = arg[1:]
        if arg.endswith("."):
            arg = arg[:-1]
        final_args.append(arg)
    parts = final_args
    if len(model_name):
        if model_name not in parts:
            parts = [model_name.lower()] + parts
    full = ".".join(parts)
    return full


def get_field_bits(obj, field_path=None):
    if field_path is None:
        field_path = ""
    attr = obj
    last_attr = obj
    bits = field_path.split(".")
    mapping = OrderedDict()
    valid = []
    skipped = []
    ignored = []
    for bit in bits:
        last_attr = attr
        attr = getattr(attr, bit, None)
        if attr is not None:
            mapping[bit] = True
            valid.append(bit)
        else:
            attr = last_attr
            mapping[bit] = False
            if not len(valid):
                ignored.append(bit)
            else:
                skipped.append(bit)
    return (attr, valid, skipped, ignored, mapping)


def get_mapped_path(od):
    bits = []
    for k, v in od.items():
        if v is True:
            bits.append(k)
        elif len(bits):
            break
    return ".".join(bits)


def get_nested_attr(obj, bits):
    attr = obj
    if isinstance(bits, str):
        bits = bits.split(".")
    for bit in bits:
        attr = getattr(attr, bit)
    return attr


class HashableList(list):
    def __hash__(self):
        return id(self)


class HashableDict(dict):
    """
    Hashable Dictionary

    Hashables should be immutable -- not enforcing this but TRUSTING you not to mutate a
    dict after its first use as a key.

    https://stackoverflow.com/questions/1151658/python-hashable-dicts
    """

    def __hash__(self):
        vals = ()
        for v in self.values():
            try:
                hash(v)
                vals += (str(v),)
            except TypeError:
                if isinstance(v, list):
                    for x in v:
                        vals += (str(x),)
                else:
                    vals += (str(v),)
        return hash((frozenset(self), frozenset(vals)))

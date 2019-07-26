from django.db.models.fields.related import (
    ManyToOneRel,
    ForeignObjectRel,
    OneToOneRel,
    ManyToManyField,
    ForeignKey,
    OneToOneField,
)
from django.db.models import Manager
from django.db.models.query import QuerySet
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


def get_real_path(obj, field_name):
    bits = field_name.split(".")
    remove = ""
    result = ""
    for i in range(len(bits) + 1):
        path = ".".join(bits[:i])
        if is_model_field(obj, path) is True:
            result = path
        elif not len(result):
            remove = path
        else:
            break
    prefix = "{}".format(remove)
    final = result.replace(prefix, "")
    if final.startswith("."):
        final = final[1:]
    return final


def get_real_field_path(obj, field_name):
    bits = field_name.split(".")
    model_name = bits.pop(0)
    non_field_name = bits.pop(-1)
    mid_path = ".".join(bits)
    field_name = mid_path.split(".", 1)[0]
    if get_class_name(obj).lower() == model_name:
        full_path = ".".join([model_name, mid_path])
    else:
        full_path = ".".join([mid_path])
    if full_path.startswith("."):
        full_path = full_path[1:]
    if full_path.endswith("."):
        full_path = full_path[:-1]
    return (full_path, field_name, non_field_name)


def assert_no_none(items, message):
    if any([x is None for x in items]):
        raise AssertionError(message)


def is_model_field(obj, field_name):
    try:
        obj = obj.model
    except AttributeError:
        pass
    if isinstance(obj, QuerySet):
        obj = obj.first()
    try:
        meta = obj._meta
        fields = meta.get_fields()
        names = [x.attname for x in fields]
        fk_name = "{}_id".format(field_name)
        if field_name in names or fk_name in names:
            return True
        return False
    except AttributeError:
        return False


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

    if isinstance(obj, QuerySet):
        for o in obj.all():
            if result is True:
                break
            result = has_circular_reference(o)
    else:
        for rel in get_rels(obj):
            if result is True:
                break
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


def get_path_variations(path):
    variations = []
    bits = path.split(".")
    for x in range(len(bits)):
        variation = ".".join(bits[:x])
        variations.append(variation)
    return variations


def remove_redundant_paths(paths):
    results = []
    for path in paths:
        redundant = False
        paths_copy = paths[:]
        paths_copy.pop(paths.index(path))
        for p in paths_copy:
            if p.startswith(path) and len(p) > len(path):
                redundant = True
        if redundant is False:
            results.append(path)
    return results


def get_class_name(obj=None):
    # Get name of parent object.
    if obj is None:
        return "Unnamed"
    else:
        return obj.__class__.__name__


def get_model_field_path(model_name, *args):
    final_args = []
    model_name = normalize_field_path(model_name)
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
        if parts[0] != model_name:
            parts = [model_name.lower()] + parts
    full = ".".join(parts)
    full = normalize_field_path(full)
    return full


def get_nested(obj, path):
    attr = obj
    attr_last = obj

    parent_path_bits = []
    child_path_bits = []
    ignored_path_bits = []
    field_name = None

    for bit in path.split("."):
        attr_last = attr
        attr = getattr(attr, bit, None)

        if attr is not None:
            parent_path_bits.append(bit)
            field_name = bit
        else:
            attr = attr_last
            if len(parent_path_bits):
                child_path_bits.append(bit)
            else:
                ignored_path_bits.append(bit)

    if isinstance(attr, Manager):
        attr = attr.all()

    suffix = ".".join(parent_path_bits)
    parent_path = path.replace(".{}".format(suffix), "")
    parent_path = normalize_field_path(parent_path)

    child_path = ".".join(child_path_bits)
    child_path = normalize_field_path(child_path)

    return (obj, parent_path, attr, child_path, field_name)


def deep_update(obj, path, value):
    dest = obj
    bits = path.split(".")
    last = bits.pop(-1)
    for bit in bits:
        if bit in dest:
            dest = dest[bit]
        else:
            dest = dest[bit] = OrderedDict()
    dest[last] = value
    return dest


def get_path_options(obj, field_path=None):
    if field_path is None:
        field_path = ""

    source_bits = field_path.split(".")

    if isinstance(obj, (Manager, QuerySet)):
        source = obj = obj.all()
    else:
        source = obj
    source_last = source

    try:
        root_model_name = source_bits.pop(0)
    except IndexError:
        root_model_name = ""

    try:
        current_model_name = source_bits.pop(0)
    except IndexError:
        current_model_name = ""

    ignored_bits = []
    child_bits = []
    host_field_bits = []
    host_field_name = ""
    child = None

    for bit in source_bits:
        print("bit: ", bit)
        source_last = source
        source = getattr(source, bit, None)

        if isinstance(source, (QuerySet, Manager)):
            source = source.all()

        if source is None:
            source = source_last

            if len(host_field_bits):
                child_bits.append(bit)
            else:
                ignored_bits.append(bit)
        else:
            host_field_name = bit

            _is_rel = is_rel(source)
            _is_rev = is_reverse_rel(source)
            _is_qs = isinstance(source, (Manager, QuerySet))

            if _is_rel or _is_rev or _is_qs:
                child = source
                source = source_last
                break
            else:
                host_field_bits.append(bit)

    if isinstance(source, (QuerySet, Manager)):
        source = source.all()

    host_field_path = ".".join([root_model_name, current_model_name] + host_field_bits)
    _, suffix = host_field_path.rsplit(".", 1)

    if is_model_field(child, suffix):
        if suffix == host_field_name:
            child_path = ".".join([suffix])
        else:
            child_path = ".".join([suffix, host_field_name])
    else:
        child_path = ""

    child_path = normalize_field_path(child_path)

    ret = {
        "source": source,
        "host_field_name": host_field_name,
        "host_field_path": host_field_path,
        "child_path": child_path,
    }
    print(ret)

    return ret


def normalize_field_path(field_path):
    if field_path.startswith("."):
        field_path = field_path[1:]
    if field_path.endswith("."):
        field_path = field_path[:-1]
    return field_path


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
    last = obj
    done = False
    used = []
    rem = []
    if isinstance(bits, str):
        bits = bits.split(".")
    while len(bits):
        if done is True:
            break
        bit = bits.pop(0)
        last = attr
        attr = getattr(attr, bit, None)
        if attr is not None:
            used.append(bit)
        else:
            attr = last
            rem.append(bit)
    ret = (attr, used, rem)
    return ret


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

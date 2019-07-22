import os
import re
from django.conf import settings
from django.conf.urls import url
from django.utils.module_loading import import_string

from .utils import ACTION_MAPS


def load_urls(
    current_file, urls=[], ignored=[], target_file="urls.py", target_attr="urlpatterns"
):
    cur_dir = os.path.dirname(os.path.abspath(current_file))
    for dir_name in os.listdir(cur_dir):
        dir_path = os.path.join(cur_dir, dir_name)
        if os.path.isdir(dir_path):
            if dir_name in ignored:
                continue
            urls_module = os.path.join(dir_path, target_file)
            if os.path.isfile(urls_module):
                rel_path = os.path.relpath(urls_module, settings.SITE_ROOT)
                rel_path = rel_path.replace(".py", "")
                module_path = rel_path.replace("/", ".")
                module_path = "{}.{}".format(module_path, target_attr)
                urls += import_string(module_path)
    return urls


def detail_route_url(viewset, lookup_field, ignored=[]):
    model = viewset.queryset.model
    name = model._meta.model_name.lower()
    name_plural = model._meta.verbose_name_plural.lower()
    name_plural_spaceless = re.sub(r"\s+", "", name_plural)
    return url(
        regex=r"^{}/(?!({})/?$)(?P<{}>[^/.]+)/?$".format(
            name_plural_spaceless, "|".join([name for name in ignored]), lookup_field
        ),
        view=viewset.as_view(actions=ACTION_MAPS["detail_route"]),
        name="{}-detail".format(name),
    )


def list_route_url(viewset):
    model = viewset.queryset.model
    name = model._meta.model_name.lower()
    name_plural = model._meta.verbose_name_plural.lower()
    name_plural_spaceless = re.sub(r"\s+", "", name_plural)
    return url(
        regex=r"^{}/?$".format(name_plural_spaceless),
        view=viewset.as_view(actions=ACTION_MAPS["list_route"]),
        name="{}-list".format(name),
    )


def make_urlpatterns(viewset, lookup_field, ignored=[]):
    return [list_route_url(viewset), detail_route_url(viewset, lookup_field, ignored)]

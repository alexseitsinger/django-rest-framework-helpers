import re
from django.conf.urls import url
from .action_maps import detail_route, list_route


def detail_route_url(viewset, lookup_field, ignored=[]):
    model = viewset.queryset.model
    name = model._meta.model_name.lower()
    name_plural = model._meta.verbose_name_plural.lower()
    name_plural_spaceless = re.sub(r"\s+", "", name_plural)
    return url(
        regex=r"^{}/(?!({})/?$)(?P<{}>[^/.]+)/?$".format(
            name_plural_spaceless,
            "|".join([name for name in ignored]),
            lookup_field,
        ),
        view=viewset.as_view(actions=detail_route),
        name="{}-detail".format(name)
    )


def list_route_url(viewset):
    model = viewset.queryset.model
    name = model._meta.model_name.lower()
    name_plural = model._meta.verbose_name_plural.lower()
    name_plural_spaceless = re.sub(r"\s+", "", name_plural)
    return url(
        regex=r"^{}/?$".format(name_plural_spaceless),
        view=viewset.as_view(actions=list_route),
        name="{}-list".format(name)
    )


def make_urlpatterns(viewset, lookup_field, ignored=[]):
    return [
        list_route_url(viewset),
        detail_route_url(viewset, lookup_field, ignored),
    ]

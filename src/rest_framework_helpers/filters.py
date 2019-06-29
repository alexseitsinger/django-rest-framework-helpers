class QuerystringFilter(object):
    def get_querystring_filter(self):
        field_names = self.get_field_names()
        filter_kwargs = {}
        for key, value in self.request.query_params.iteritems():
            if key in field_names:
                filter_kwargs[key] = value
        return filter_kwargs

    def get_queryset(self):
        queryset = super().get_queryset()
        querystring_filter = self.get_querystring_filter()
        queryset = queryset.filter(**querystring_filter)
        return queryset

from rest_framework.pagination import PageNumberPagination


class VariablePageSizePagination(PageNumberPagination):
    @classmethod
    def create(cls,
               page_size,
               page_size_query_param="page_size",
               max_page_size=None):
        if max_page_size is None:
            max_page_size = page_size
        instance = cls
        instance.page_size = page_size
        instance.page_size_query_param = page_size_query_param
        instance.max_page_size = max_page_size
        return cls


class FiftyResultsPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 50


class OneHundredResultsPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 100

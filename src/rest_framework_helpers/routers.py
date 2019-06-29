from rest_framework import routers


class ExtendableRouter(routers.DefaultRouter):
    """
    Extends `DefaultRouter` class to add a method for extending url routes from another router.

    https://stackoverflow.com/questions/31483282/django-rest-framework-combining-routers-from-different-apps
    """

    def extend(self, router):
        """
        Extend the routes with url routes of the passed in router.

        Args:
             router: SimpleRouter instance containing route definitions.
        """
        self.registry.extend(router.registry)

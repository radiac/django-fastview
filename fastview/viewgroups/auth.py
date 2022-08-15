from typing import Any, Dict, List

from django.contrib.auth.urls import urlpatterns as auth_urlpatterns
from django.urls import path
from django.urls.resolvers import URLPattern
from django.views.generic.base import TemplateResponseMixin, TemplateView

from .base import ViewGroup


class AuthViewGroup(ViewGroup):
    """
    Django auth views

    Based on django.contrib.auth.urls, but with default templates supplied
    """

    template_root = "fastview/auth"

    def get_urls(self):
        urlpatterns: List[URLPattern] = []
        url_pattern: URLPattern
        template_root = self.get_template_root()

        # Step through django.contrib.auth.urls and rewrite them for our templates
        for url_pattern in auth_urlpatterns:
            # Sanity check that Django hasnn't changed what it's doing
            if not isinstance(url_pattern, URLPattern):
                raise ValueError("Unexpected URL pattern in auth urls")

            if not issubclass(
                getattr(url_pattern.callback, "view_class"),
                (TemplateView, TemplateResponseMixin),
            ):
                raise ValueError("Unexpected URL callback in auth urls")

            view_cls: TemplateView = url_pattern.callback.view_class
            view_initkwargs: Dict[str, Any] = url_pattern.callback.view_initkwargs
            new_kwargs = view_initkwargs.copy()
            template_name = view_cls.template_name
            if template_root is not None:
                template_name = template_name.replace(
                    "registration/",
                    f"{template_root}/",
                )
            new_kwargs["template_name"] = template_name
            urlpatterns.append(
                path(
                    route=url_pattern.pattern._route,
                    view=view_cls.as_view(**new_kwargs),
                    kwargs=url_pattern.default_args,
                    name=url_pattern.name,
                )
            )

        return urlpatterns

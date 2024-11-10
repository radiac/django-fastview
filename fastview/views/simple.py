"""
Simple views, equivalent to django.views.base
"""
from __future__ import annotations

from typing import Callable, Self

from django import views
from django.contrib.auth.mixins import UserPassesTestMixin

from .mixins import AbstractFastView


def group_view(**kwargs) -> Callable | AbstractFastView:
    """
    Decorator wrapper for FunctionView.from_fn()

    Usage::

        class MyViewGroup(ViewGroup):
            @group_view(url_pattern="{name}/")
            def example_view(self, request):
                ...
    """

    def wrap(fn):
        return FunctionView.from_fn(fn, **kwargs)

    # Called
    return wrap


class FunctionView(AbstractFastView, views.View):
    view_fn: Callable

    @classmethod
    def from_fn(cls, view, **kwargs) -> type[Self]:
        def wrapped(*args, **kwargs):
            return staticmethod(view)(cls.viewgroup, *args, **kwargs)

        view_cls = type(view.__name__, (cls,), {"view_fn": wrapped, **kwargs})
        return view_cls

    def http_method_not_allowed(self, request, *args, **kwargs):
        """
        No specific method to handle this request; pass it into the FBV
        """
        return self.view_fn(request, *args, **kwargs)

"""
URL management
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional
from urllib.parse import urlencode

from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse


if TYPE_CHECKING:
    from .views.mixins import AbstractFastView


def _reverse(
    viewname: str,
    view: AbstractFastView,
    *args,
    **kwargs,
) -> str:
    """
    Reverse a URL in the context of the current view and viewgroup
    """
    if viewname.startswith(":"):
        if not view:
            raise ValueError("Cannot reverse a viewgroup URL without a view")

        if not view.viewgroup:
            raise ImproperlyConfigured(
                "Cannot reverse a viewgroup URL outside a viewgroup."
            )

        namespace = view.request.resolver_match.namespace

        # Look up view
        viewname = viewname[1:]
        view_cls = view.viewgroup.views.get(viewname)
        if not view_cls:
            raise ImproperlyConfigured(f"Viewgroup does not define a {viewname} view.")

        from .views.mixins import ObjectFastViewMixin

        if issubclass(view_cls, ObjectFastViewMixin):
            object = getattr(view, "object", None)
            if not object:
                raise ImproperlyConfigured("Could not find target object on the view")

            return reverse(f"{namespace}:{viewname}", args=[object.pk])

        return reverse(f"{namespace}:{viewname}")

    return reverse(viewname, *args, **kwargs)


def viewgroup_reverse(
    viewname: str,
    view: AbstractFastView,
    *args,
    params: Optional[Dict[str, str]] = None,
    **kwargs,
) -> str:
    """
    Perform a url reverse() in the context of the current view and viewgroup

    Args:

        viewname (str): The name of the view to resolve
            Start the ``viewname`` with a colon to refer to views in the ``view``'s
            viewgroup, eg::

                self.reverse(":index") self.reverse(":detail") self.reverse(":update")

            If a viewgroup view operates on an object (subclasses ObjectFastViewMixin),
            the ``view.object`` will be used for path resolution.

            If the viewname does not start with a colon, standard reverse() will be
            called.

        view (AbstractFastView): The current view being processed. Required if
            ``viewname`` starts with a colon.

        params (dict): Optional dictionary of params to encode in the querystring

        *args: Standard arguments for reverse()
        **kwargs: Standard keyword arguments for reverse()
    """
    url = _reverse(viewname, view, *args, **kwargs)
    if params:
        encoded_params = urlencode(params)
        url = f"{url}?{encoded_params}"
    return url

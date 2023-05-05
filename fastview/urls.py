"""
URL management
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional
from urllib.parse import urlencode

from django.core.exceptions import ImproperlyConfigured
from django.http import QueryDict
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

                viewgroup_reverse(":index", view=self)
                viewgroup_reverse(":detail", view=self)
                viewgroup_reverse(":update", view=self)

            If a viewgroup view operates on an object (subclasses ObjectFastViewMixin),
            the ``view.object`` will be used for path resolution.

            If the viewname does not start with a colon, standard reverse() will be
            called.

        view (AbstractFastView): The current view being processed. Required if
            ``viewname`` starts with a colon.

        params (dict): Optional dictionary of params to encode in the querystring

        *args: Standard arguments for reverse()
        **kwargs: Standard keyword arguments for reverse()

    Returns:
        str: URL to the view
    """
    url = _reverse(viewname, view, *args, **kwargs)
    if params:
        encoded_params = urlencode(params)
        url = f"{url}?{encoded_params}"
    return url


def urlparams(params: QueryDict | None, **kwargs: Any) -> str:
    """
    Update the params in ``params`` with the new values in ``kwargs`` and return an
    URL-encoded string, preserving other params.

    Available in a template with {% load fastview %}{% urlparams .. %}

    Args:

        params (QueryDict): The existing parameters. Usually ``request.GET``.
        **kwargs (dict): New parameters to add to ``params``.
            Pass a ``None`` value to remove an existing param if it exists

    Returns:
        str: An url-encoded string ready to append to a URL
    """
    # Shallow copy so we don't have side effects
    if isinstance(params, QueryDict):
        params = params.copy()
    elif params is None:
        params = QueryDict().copy()

    # Can't call params.update() - a QueryDict appends to existing, doesn't overwrite
    for key, value in kwargs.items():
        if value is None:
            if value in params:
                del params[key]
        else:
            params[key] = value

    querystring = params.urlencode()
    return querystring

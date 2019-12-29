"""
Annotated objects
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Type

from django.db.models import Model
from django.urls import reverse


if TYPE_CHECKING:
    from .mixins import ModelFastViewMixin


class AnnotatedObject:
    # Current view - must be overridden in subclass - see for_view()
    view: ModelFastViewMixin

    def __init__(self, instance: Model):
        self.original = instance

    @classmethod
    def for_view(cls, view: Type[ModelFastViewMixin]):
        """
        Generate a version of this class to fit the given view, model and viewgroup

        This populates the subclass with the following additional methods:

            can_VIEW: if the user can access the specific ``VIEW``, eg ``can_change()``.
                One for each view on the viewgroup.
            get_VIEW_url: the url to access the ``VIEW``, eg ``get_change_url()``.
                One for each view on the viewgroup.
        """

        def can_factory(to_view):
            """
            Generate view-specific can() methods for the instance
            """

            def can(self):
                if to_view.permission.check(self.view.request, self.original):
                    return True
                return False

            return can

        def get_url_factory(to_name):
            """
            Generate view-specific get_X_url() methods for the instance
            """

            def get_url(self):
                namespace = self.view.request.resolver_match.namespace
                full_name = f"{namespace}:{to_name}"
                return reverse(full_name, args=[self.original.pk])

            return get_url

        def labels(self):
            """
            Return the field names
            """
            return self.view.labels

        def values(self):
            """
            Return the field values
            """
            return [field.get_value(self.original) for field in self.view.fields]

        def items(self):
            """
            Return (label, value) pairs
            """
            return zip(self.labels, self.values)

        # Attach functions for data values using same patterns as a dict
        attrs = {"view": view, "labels": labels, "values": values, "items": items}

        # TODO: This should probably be in the viewgroup for consistency
        # Attach list of permissions and urls to this object for object-specific views
        viewgroup = getattr(view, "viewgroup", None)
        if viewgroup:
            for name, view in viewgroup.views.items():
                if view.has_id_slug:
                    attrs[f"can_{name}"] = can_factory(view)
                    attrs[f"get_{name}_url"] = get_url_factory(name)

        # Create the new AnnotatedModel subclass
        subclass = type(f"Annotated{view.model.__name__}", (cls,), attrs)
        return subclass

"""
Annotated objects
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Type

from django.db.models import Model
from django.urls import reverse


if TYPE_CHECKING:
    from .mixins import ModelFastViewMixin


class AnnotatedObject:
    # Current view - must be overridden in subclass - see for_view()
    view: ModelFastViewMixin

    def __init__(self, instance: Model):
        """
        Arguments:
            instance: Object which this is annotating
        """
        self.original = instance

    @classmethod
    def for_view(
        cls, view: Type[ModelFastViewMixin], action_links: Optional[List[str]] = None
    ):
        """
        Generate a version of this class to fit the given view, model and viewgroup

        Arguments:
            instance: Object which this is annotating
            action_links: List of action names to filter ``.action_links``. If ``None``,
                show all.

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
            return zip(self.labels(), self.values())

        # Attach functions for data values using same patterns as a dict
        attrs = {"view": view, "labels": labels, "values": values, "items": items}

        # TODO: This should probably be in the viewgroup for consistency
        # Attach list of permissions and urls to this object for object-specific views
        viewgroup = getattr(view, "viewgroup", None)
        action_link_data = []
        if viewgroup:
            for name, to_view in viewgroup.get_object_views().items():
                can = can_factory(to_view)
                get_url = get_url_factory(name)
                attrs[f"can_{name}"] = can
                attrs[f"get_{name}_url"] = get_url
                if (
                    action_links is None or name in action_links
                ) and name != view.action:
                    action_link_data.append(
                        (name, to_view.get_action_label(), can, get_url)
                    )

        # If action links were specified, sort them into that order
        if action_links is not None:
            action_links_list = action_links  # because mypy thought it could be None
            action_link_data = sorted(
                action_link_data, key=lambda data: action_links_list.index(data[0])
            )

        attrs["action_link_data"] = action_link_data

        # Create the new AnnotatedModel subclass
        subclass = type(f"Annotated{view.model.__name__}", (cls,), attrs)
        return subclass

    def action_links(self):
        """
        Return a list of (label, url) tuples for actions that can be performed on this
        object
        """
        return [
            (label, get_url(self))
            for name, label, can, get_url in self.action_link_data
            if can(self)
        ]

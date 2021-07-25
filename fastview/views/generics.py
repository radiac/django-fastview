"""
Generic views for FastView
"""

from __future__ import annotations

from typing import Dict, Optional

from django.views import generic

from ..constants import PARAM_LIMIT, PARAM_ORDER
from .display import ObjectValue
from .filters import Filter
from .mixins import (
    DisplayFieldMixin,
    FormFieldMixin,
    InlineMixin,
    ModelFastViewMixin,
    ObjectFastViewMixin,
    SuccessUrlMixin,
)


class ListView(DisplayFieldMixin, ModelFastViewMixin, generic.ListView):
    """
    A permission-aware ListView with support for ViewGroups

    The template context has additional variables available:

        annotated_object_list: List of (object, Can, fields) tuples
    """

    default_template_name = "fastview/list.html"
    title = "{verbose_name_plural}"
    fields = [ObjectValue()]
    action = "list"
    action_label = "List"
    row_permission = None
    filters: Optional[Dict[str, Filter]] = None

    def get_queryset(self):
        qs = super().get_queryset()

        # Only show permitted objects
        if self.row_permission:
            qs = self.row_permission.filter(request=self.request, queryset=qs)

        if self.request.GET:
            # Filter
            if self.filters is not None:
                for param_name, filter_obj in self.filters.items():
                    if param_name in self.request.GET:
                        qs = filter_obj.process(qs, self.request.GET[param_name])

            # Order
            ordering = self.get_ordering()
            if ordering:
                qs = qs.order_by(*ordering)

            # Limit the queryset
            limit = self.request.GET.get(PARAM_LIMIT, 0)
            if limit:
                try:
                    limit = int(limit)
                except ValueError:
                    limit = 0

                # Ensure positive limit (or 0)
                limit = max(0, limit)

                if limit:
                    qs = qs[:limit]

        return qs

    def get_ordering(self):
        """
        Order by the CSV list in the query string parameter PARAM_ORDER
        """
        if PARAM_ORDER not in self.request.GET:
            return None

        # Validate slugs, get Display objects, and build list of order fields
        slugs = self.request.GET[PARAM_ORDER].split(",")
        ordering = []
        for slug in slugs:
            order = ""
            if slug.startswith("-"):
                order = "-"
                slug = slug[1:]
            if slug not in self._slug_to_field:
                raise ValueError(f"Invalid order field {slug}")
            field_name = self._slug_to_field[slug].get_order_by()
            ordering.append(f"{order}{field_name}")

        return ordering

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Generator to return object list with permissions and iterable fields
        context["annotated_object_list"] = self.annotated_object_list_generator_factory(
            context["object_list"]
        )

        return context

    def annotated_object_list_generator_factory(self, object_list):
        """
        Generate an annotated object list without holding everything in memory

        Returns:
            A generator factory to annotate an object list.

        In other words:

        * This takes a list of objects
        * It returns a clean generator function to iterate over those objects
        * It is not called until it reaches the template
        * It will be called each time it is referenced in the template, creating a
          clean generator, allowing the list to be iterated over more than once in the
          same template.
        * The generator yields ``AnnotatedObject`` objects for rendering
        """

        AnnotatedModelObject = self.get_annotated_model_object()

        def generator():
            for obj in object_list:
                yield AnnotatedModelObject(obj)

        return generator


class DetailView(DisplayFieldMixin, ObjectFastViewMixin, generic.DetailView):
    title = "{object}"
    default_template_name = "fastview/detail.html"
    has_id_slug = True
    action = "view"
    action_label = "View"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        AnnotatedModelObject = self.get_annotated_model_object()
        context["annotated_object"] = AnnotatedModelObject(context["object"])
        return context


class CreateView(
    SuccessUrlMixin,
    FormFieldMixin,
    InlineMixin,
    ObjectFastViewMixin,
    generic.CreateView,
):
    title = "{action} {verbose_name}"
    default_template_name = "fastview/create.html"
    action = "create"
    action_label = "Add"


class UpdateView(
    SuccessUrlMixin,
    FormFieldMixin,
    InlineMixin,
    ObjectFastViewMixin,
    generic.UpdateView,
):
    title = "{action} {verbose_name}"
    default_template_name = "fastview/update.html"
    has_id_slug = True
    action = "update"
    action_label = "Change"


class DeleteView(SuccessUrlMixin, ObjectFastViewMixin, generic.DeleteView):
    title = "{action} {verbose_name}"
    default_template_name = "fastview/delete.html"
    has_id_slug = True
    action = "delete"
    action_label = "Delete"

"""
Generic views for FastView
"""

from __future__ import annotations

from typing import Dict, List, Optional, Union

import django
from django.contrib import messages
from django.core.exceptions import FieldDoesNotExist
from django.db.models import Q, QuerySet
from django.views import generic

from ..constants import PARAM_LIMIT, PARAM_ORDER, PARAM_SEARCH
from .display import ObjectValue
from .filters import BaseFilter, FilterError, field_to_filter_class
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
    """

    #: The default template name
    default_template_name = "fastview/list.html"

    #: The default fragment template name
    #: Used for fragment rendering and directly in the container template
    # fragment_template_name = "fastview/fragments/list.html"

    #: The page title, passed to template context for use in page title and headers.
    #: See :meth:`get_title` for more details
    title = "{verbose_name_plural}"

    #: List of fields to show in the list table.
    #:
    #: The values can be :mod:`display classes <fastview.views.display>` or string
    #  values which correspond to model field names or methods on the model.
    #:
    #: Example::
    #:
    #:      fields = [
    #:          'field_name',  # MyModel.field_name
    #:          'get_value',  # MyModel.get_value()
    #:          CustomValue(),  # :class:`fastview.views.display.DisplayValue` subclass
    #:
    #: Defaults to show the string value of the model instance
    fields = [ObjectValue()]

    #: Name of action for the ViewGroup
    action = "list"

    #: Label for this action
    action_label = "List"

    #: :mod:`Permission <fastview.permissions>` check to display individual rows.
    row_permission = None

    #: List of available filters to apply to the list table.
    #:
    #: The values can be :mod:`filter classes <fastview.views.filters>` or string values
    #: which correspond to model field names.
    #:
    #: Example::
    #:
    #:      filters = [
    #:          'field_name',  # MyModel.field_name
    #:          CustomFilter(...), # :class:`fastview.views.filters.Filter` subclass
    filters: Optional[List[Union[str, BaseFilter]]] = None

    #: List of fields to search
    search_fields: Optional[List[str]] = None

    #: Context variable name for the annotated object list.
    context_annotated_name = "annotated_object_list"

    #: Ordering params found in the request when getting the queryset
    request_ordering: Optional[Dict[str, str]] = None

    def dispatch(self, request, *args, **kwargs):
        # Set up request caches here in case a subclass overrides something carelessly
        self.request_filters = {}
        self.request_ordering = {}
        return super().dispatch(request, *args, **kwargs)

    def get_filters(self) -> Dict[str, BaseFilter]:
        """
        Build filter list by looking up field strings and converting to Filter instances

        Convert self.filters from::

            ['field_name', Filter('param', ...)]

        to::

            {
                'field_name': Filter('field_name', ...),
                'param': Filter('param', ...),
            }
        """
        filters: Dict[str, BaseFilter] = {}
        if not self.filters:
            return filters

        for filter_obj in self.filters:
            if not isinstance(filter_obj, BaseFilter):
                # Convert field name into a filter object
                field_name = filter_obj
                try:
                    field = self.model._meta.get_field(field_name)
                except FieldDoesNotExist as e:
                    # Extend error message so it's a bit more helpful
                    e.args = (f"Filter invalid: {e.args[0]}",) + e.args[1:]
                    raise e
                filter_cls = field_to_filter_class(field)
                filter_obj = filter_cls(field_name)

            # Give the filter a reference to this view
            filter_obj.view = self
            filters[filter_obj.param] = filter_obj

        return filters

    def get_queryset(self) -> QuerySet:
        """
        Apply filters, search terms, ordering and limits to the queryset
        """
        qs = super().get_queryset()

        # Only show permitted objects
        if self.row_permission:
            qs = self.row_permission.filter(request=self.request, queryset=qs)

        # Collect list of filter definitions and put them on `.request_filters` so we
        # can use them when rendering the template
        self.request_filters = self.get_filters()

        # If we have filters defined, check GET and default filter
        if self.request_filters:
            for param, filter_obj in self.request_filters.items():
                if param in self.request.GET:
                    # Bind filters to values for use in templates
                    try:
                        bound_filter = filter_obj.bind(self.request.GET[param])
                        self.request_filters[param] = bound_filter

                        # Call the filters' process() to filter the data
                        qs = bound_filter.process(qs)

                    except FilterError as e:
                        messages.error(self.request, str(e))

        # Search
        search_query = self.request.GET.get(PARAM_SEARCH, "")
        if search_query:
            qs = self.search_queryset(search_query, qs)

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

    def search_queryset(self, search_query: str, qs: QuerySet) -> QuerySet:
        if not self.search_fields:
            return qs

        rules = Q()
        for field in self.search_fields:
            # Add __icontains to the field, unless it already specifies a string rule
            if "__" in field:
                suffix = field.rsplit("__", 1)[1]
            else:
                suffix = ""
            if not suffix or suffix not in [
                "exact",
                "iexact",
                "contains",
                "icontains",
                "startswith",
                "istartswith",
                "endswith",
                "iendswith",
            ]:
                field = f"{field}__icontains"
            rules |= Q(**{field: search_query})

        qs = qs.filter(rules)
        return qs

    def get_ordering(self):
        """
        Build queryset ordering rule from the CSV list of DisplayValue slugs in
        ``request.GET[PARAM_ORDER]``
        """
        if PARAM_ORDER not in self.request.GET:
            return None

        # Split CSV list into DV slugs
        slugs = self.request.GET[PARAM_ORDER].split(",")
        ordering = []
        for slug in slugs:
            # Determine order for this slug
            order = ""
            if slug.startswith("-"):
                order = "-"
                slug = slug[1:]
            self.request_ordering[slug] = order

            # Find DisplayValue for this slug, and build ordering rule
            displayvalue = self.resolve_displayvalue_slug(slug)
            field_name = displayvalue.get_order_by(self)
            ordering.append(f"{order}{field_name}")

        return ordering

    def get_context_data(self, **kwargs):
        """
        The template context has additional variables available::

            annotated_object_list: List of (object, Can, fields) tuples
            filters: List of filters, bound to any query arguments
            page_range: Paginator page range (Django 3.2+)
            label_orders: List of (label, current_order, param_value) tuples for
                links in the table header
        """
        context = super().get_context_data(**kwargs)
        if self.paginate_by:
            page_obj = context["page_obj"]
            if django.VERSION >= (3, 2, 0):
                context["page_range"] = page_obj.paginator.get_elided_page_range(
                    page_obj.number
                )
            objects = page_obj
        else:
            objects = context["object_list"]

        # Generator to return object list with permissions and iterable fields
        context[self.context_annotated_name] = self.object_annotator_factory(objects)

        context["filters"] = self.request_filters.values()

        context["label_orders"] = []
        for field in self.get_fields():
            label = field.get_label(self)
            slug = field.get_slug(self)
            current_order = self.request_ordering.get(slug, None)
            if current_order is None or current_order == "-":
                param_value = slug
            else:
                param_value = f"-{slug}"
            context["label_orders"].append((label, current_order, param_value))

        context["PARAM_SEARCH"] = PARAM_SEARCH

        return context

    def object_annotator_factory(self, object_list):
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

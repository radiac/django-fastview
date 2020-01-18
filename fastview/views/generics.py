"""
Generic views for FastView
"""

from __future__ import annotations

from django.views import generic

from .display import ObjectValue
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
    action = "upoate"


class DeleteView(SuccessUrlMixin, ObjectFastViewMixin, generic.DeleteView):
    title = "{action} {verbose_name}"
    default_template_name = "fastview/delete.html"
    has_id_slug = True
    action = "delete"

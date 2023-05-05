"""
Support for django-tagulous tag fields
"""

from typing import Optional, Tuple

from django.db import models
from django.utils.safestring import mark_safe

from tagulous.models.models import TagTreeModel

from ..urls import urlparams, viewgroup_reverse
from ..views.display import AttributeValue
from ..views.filters import FilterError, TreeFilter, TreeListType


class TagulousLinksValue(AttributeValue):
    """
    DisplayValue for Tagulous tag fields

    Usage::

        index_view = dict(
            fields=[TagulousLinksValue("tags"), ...],
        )
    """

    def get_value(self, view, instance):
        tags = getattr(instance, self.attribute)

        # See if we are on the list view
        list_url = viewgroup_reverse(":index", view=view)
        if view.request.path == list_url:
            params = view.request.GET

            # Exclude pagination so we don't end up on an invalid page
            params.pop("page", None)
        else:
            params = None

        pattern = f'<a href="{list_url}?{{params}}">{{tag}}</a>'

        tag_urls = [
            pattern.format(
                params=urlparams(
                    params,
                    **{
                        self.attribute: tag.path
                        if isinstance(tag, TagTreeModel)
                        else tag.slug
                    },
                ),
                tag=tag,
            )
            for tag in tags.all()
        ]
        return mark_safe("<br>".join(tag_urls))


class TagulousTreeFilter(TreeFilter):
    """
    Tree filter for Tagulous tag fields in tree mode

    Usage::

        index_view = dict(
            filters=[TagulousTreeFilter("tags"), ...],
        )
    """

    _tree: Optional[TreeListType] = None

    def get_tree(self):
        if self._tree is not None:
            return self._tree

        tree = self.tree
        if tree is None:
            related_model = self.model_field.related_model
            if not issubclass(related_model, TagTreeModel):
                raise FilterError(
                    f"Filter {self.label} expected a relationship to a TagTreeModel"
                )
            tree = related_model.objects.as_nested_list()

        tree = [self.get_all_choice()] + tree
        self._tree = tree
        return tree

    def _choice_to_value_label(self, tag) -> Tuple[str, str]:
        return (tag.path, tag.label)

    def process(self, qs: models.QuerySet) -> models.QuerySet:
        """
        Filter the queryset using the bound value
        """
        if self.value:
            qs = qs.filter(**{f"{self.field_name}__path__startswith": self.value})
        return qs

    def get_all_choice(self):
        value, label = super().get_all_choice()
        model = self.model_field.related_model
        return (model(path=value, label=label), [])

    @property
    def as_title(self):
        parts = self.value.split("/")
        words = [part.title() for part in parts]
        return " › ".join(words)

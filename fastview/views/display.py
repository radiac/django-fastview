"""
Display values
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from django.db.models import Model


if TYPE_CHECKING:
    from .mixins import DisplayFieldMixin


class DisplayValue:
    def get_label(self, view: DisplayFieldMixin) -> str:
        raise NotImplementedError()

    def get_value(self, instance: Model) -> Any:
        raise NotImplementedError()


class AttributeValue(DisplayValue):
    """
    Return an attribute of the object
    """

    attribute: str
    label: Optional[str]

    def __init__(self, attribute, label=None):
        self.attribute = attribute
        self.label = label

    def get_label(self, view: DisplayFieldMixin) -> str:
        if self.label is not None:
            return self.label
        return self.attribute.replace("_", " ").title()

    def get_value(self, instance: Model) -> Any:
        # TODO: Smart return values for better rendering:
        #   choices should use get_x_display()
        #   map booleans to icons - render a template, or format a settings string
        #   newline textfields
        #   format numbers (should return a str)
        return getattr(instance, self.attribute)


class ObjectValue(DisplayValue):
    def get_label(self, view: DisplayFieldMixin) -> str:
        return view.model._meta.verbose_name.title

    def get_value(self, instance: Model) -> Any:
        return str(instance)

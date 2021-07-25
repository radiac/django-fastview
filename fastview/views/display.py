"""
Display values
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from django.db.models import Manager, Model
from django.utils.text import slugify


if TYPE_CHECKING:
    from .mixins import DisplayFieldMixin


def snake_slugify(value: str) -> str:
    return slugify(value).replace("-", "_")


class DisplayValue:
    def get_label(self, view: DisplayFieldMixin) -> str:
        """
        Return a label for this field
        """
        raise NotImplementedError()

    def get_slug(self, view: DisplayFieldMixin) -> str:
        """
        Return a slug for this field, for use in ordering
        """
        return snake_slugify(self.get_label(view))

    def get_value(self, instance: Model) -> Any:
        """
        Return the value as a safe HTML string
        """
        raise NotImplementedError()

    def order_by(self) -> str:
        """
        Return the value as a safe HTML string
        """
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
        value = getattr(instance, self.attribute)
        if isinstance(value, Manager):
            value = "\n".join(str(obj) for obj in value.all())
        return value

    def get_order_by(self) -> str:
        """
        Return field name for order_by(..)
        """
        return self.attribute


class ObjectValue(DisplayValue):
    """
    Return the string representation of the object
    """

    def get_label(self, view: DisplayFieldMixin) -> str:
        return view.model._meta.verbose_name.title

    def get_value(self, instance: Model) -> Any:
        return str(instance)

    def get_order_by(self) -> str:
        return "pk"

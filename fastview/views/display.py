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

    def get_order_by(self, view: DisplayFieldMixin) -> str:
        """
        Return the value as a safe HTML string
        """
        raise NotImplementedError()


class AttributeValue(DisplayValue):
    """
    Display an attribute of the object
    """

    attribute: str
    label: Optional[str]
    order_by: Optional[str]

    def __init__(self, attribute, label=None, order_by=None):
        """
        Args:
            attribute (str): The object attribute to display

            label (:obj:`str`, optional): The label to use when displaying this value

            order_by (:obj:`str`, optional): The object attribute to order by - see
                :func:`get_order_by`
        """
        self.attribute = attribute
        self.label = label
        self.order_by = order_by

    def get_label(self, view: DisplayFieldMixin) -> str:
        """
        Return the label to use when displaying this value

        Priority is given to a `label` set by :func:`__init__`

        If not set, it will honour Django's admin syntax by looking for a
        ``short_description`` attribute on the view's model, eg::

            class MyModel(models.Model):
                full_name = models.CharField(max_length=255)

                def get_first_name(self):
                    return full_name.split(" ")[0]

                get_first_name.short_description = "First name")

        If that is not found, it will title case the attribute name then replace ``_``
        with a space eg::

            value = AttributeValue("full_name")
            # value.get_label(view) will return "Full name"
        """
        # Explicit label has priority
        if self.label is not None:
            return self.label

        # If we're operating on a model, check for a Django admin attribute we can reuse
        if hasattr(view, "model"):
            attr = getattr(view.model, self.attribute)
            if hasattr(attr, "short_description"):
                return attr.short_description

        return self.attribute.title().replace("_", " ")

    def get_value(self, instance: Model) -> Any:
        # TODO: Smart return values for better rendering:
        #   choices should use get_x_display()
        #   map booleans to icons - render a template, or format a settings string
        #   newline textfields
        #   format numbers (should return a str)
        value = getattr(instance, self.attribute)
        if isinstance(value, Manager):
            value = "\n".join(str(obj) for obj in value.all())
        if callable(value):
            value = value()
        return value

    def get_order_by(self, view: DisplayFieldMixin) -> str:
        """
        Return field name for order_by(..)

        Priority is given to an `order_by` set by :func:`__init__`.

        If not set, it will honour Django's admin syntax by looking for a
        ``admin_order_field`` attribute on the attribute on the view's model, eg::

            class MyModel(models.Model):
                foo = models.IntegerField()

                def bar(self):
                    return self.foo + 1

                bar.admin_order_field = "foo"

        If not set, it will default to the attribute itself, eg::

            value = AttributeValue("foo")
            # value.get_order_by(view) will return "foo"
        """
        # Explicit order_by has priority
        if self.order_by is not None:
            return self.order_by

        # If we're operating on a moedl, check for a Django admin attribute we can reuse
        if hasattr(view, "model"):
            attr = getattr(view.model, self.attribute)
            if hasattr(attr, "admin_order_field"):
                return attr.admin_order_field

        return self.attribute


class ObjectValue(DisplayValue):
    """
    Return the string representation of the object
    """

    def get_label(self, view: DisplayFieldMixin) -> str:
        return view.model._meta.verbose_name.title

    def get_value(self, instance: Model) -> Any:
        return str(instance)

    def get_order_by(self, view: DisplayFieldMixin) -> str:
        return "pk"

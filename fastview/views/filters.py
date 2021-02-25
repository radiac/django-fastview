from typing import Any, Iterable, Optional, Tuple

from django.db import models
from django.forms import fields


class Filter:
    """
    Filter queryset based on a value
    """

    field_name: str
    label: str
    faceted: bool

    field_cls = fields.CharField
    """
    Form field class used to clean and validate raw param data
    """

    def __init__(self, field_name: str, label: str = None):
        """
        Initialise the filter

        Args:
            field_name: Name of field on model to use for filter
            label: Optional label; will default to title-cased field_name
            choices: Choices for display, and for form field class validation (if applicable)
        """
        self.field_name = field_name
        self.label = label or field_name.title()

    def get_field(self):
        field = self.field_cls(**self.get_field_options())
        return field

    def get_field_options(self):
        return {}

    def process(self, qs: models.QuerySet, value: Any):
        field = self.get_field()
        cleaned = field.clean(value)
        qs = qs.filter(**self.get_filter_kwargs(cleaned))
        return qs

    def get_filter_kwargs(self, cleaned):
        return {self.field_name: cleaned}


class ChoiceFilter(Filter):
    choices: Optional[Iterable[Tuple[Any, str]]]
    field_cls = fields.ChoiceField

    def __init__(
        self,
        field_name: str,
        label: str = None,
        choices: Optional[Iterable[Tuple[Any, str]]] = None,
    ):
        """
        Initialise the filter

        Args:
            field_name: Name of field on model to use for filter
            label: Optional label; will default to title-cased field_name
            choices: Choices for display, and for form field class validation (if applicable)
        """
        super().__init__(field_name, label)
        self.choices = choices

    def get_field_options(self):
        return {"choices": self.get_choices()}

    def get_choices(self):
        return self.choices


class ForeignKeyFilter(Filter):
    pass


class DateFilter(Filter):
    field_cls = fields.DateField

    def get_field_options(self):
        return {}


class FutureDateFilter(DateFilter):
    """
    Filter down to dates including and after the specified date
    """

    def get_filter_kwargs(self, cleaned):
        return {f"{self.field_name}__gte": cleaned}


class PastDateFilter(DateFilter):
    """
    Filter down to dates including and before the specified date
    """

    def get_filter_kwargs(self, cleaned):
        return {f"{self.field_name}__lte": cleaned}


class BooleanFilter(ChoiceFilter):
    """
    Filter a boolean yes/no field
    """

    field_cls = fields.BooleanField
    choices = ((1, "Yes"), (0, "No"))

    def get_field_options(self):
        return {"required": False}

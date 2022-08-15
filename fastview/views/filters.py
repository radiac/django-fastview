from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Type

from django.db import models
from django.template.loader import get_template
from django.utils.functional import cached_property
from django.utils.translation import gettext as _


if TYPE_CHECKING:
    from .mixins import AbstractFastView


class FilterError(ValueError):
    pass


ChoiceType = Tuple[str, str]
ChoicesType = List[ChoiceType]
TreeListType = List[Tuple[ChoiceType, "TreeListType"]]  # type: ignore
# Recursive typing not current supported by mypy https://github.com/python/mypy/issues/731


class BaseFilter:
    """
    Base filter with arbitrary text matching
    """

    view: Optional[AbstractFastView] = None
    param: str
    field_name: str
    label: str
    value: str = ""
    template_name: str = "fastview/filters/choices.html"
    ignore_invalid: bool = False

    def __init__(
        self,
        param: str,
        field_name: Optional[str] = None,
        label: Optional[str] = None,
    ):
        self.param = param
        self.field_name = field_name or param

        if label:
            self.label = label
        else:
            self.label = param.replace("_", " ").title()

    def bind(self, value: Any) -> BaseFilter:
        """
        Create a copy of this filter and bind it to a submitted value

        The value will be cleaned by bound.set_value
        """
        bound = self.clone()
        bound.set_value(value)
        return bound

    def deconstruct(self) -> Dict[str, Any]:
        """
        Create a dict of arguments for the constructor, used by clone()
        """
        kwargs = {
            "param": self.param,
            "label": self.label,
            "field_name": self.field_name,
        }

        return kwargs

    def clone(self) -> BaseFilter:
        """
        Make a clean copy of this filter, without a value
        """
        kwargs = self.deconstruct()
        cloned = type(self)(**kwargs)
        cloned.view = self.view
        return cloned

    def set_value(self, value: str):
        """
        Clean a value and store it
        """
        self.value = value

    def get_template_name(self):
        """
        Return the template name for showing this filter in the frontend
        """
        return self.template_name

    def render(self) -> str:
        """
        Render the template for the frontend
        """
        template_name = self.get_template_name()
        template = get_template(template_name)
        context = self.get_context()
        return template.render(context)

    def get_context(self) -> Dict["str", Any]:
        context = {
            "filter": self,
        }
        return context

    def get_all_choice(self) -> ChoiceType:
        """
        Return an "All" option (value, label) tuple
        """
        return ("", _("All"))

    @cached_property
    def model(self):
        if not self.view:
            raise FilterError(
                f"Filter {self.label} initiated incorrectly, view unknown"
            )
        if not hasattr(self.view, "model"):
            raise FilterError(f"View for filter {self.label} has no model")
        return self.view.model

    @cached_property
    def model_field(self):
        try:
            field = self.model._meta.get_field(self.field_name)
        except models.FieldDoesNotExist:
            raise FilterError(
                f"Named field for filter {self.label} does not match a model field"
            )

        return field

    def process(self, qs: models.QuerySet) -> models.QuerySet:
        """
        Filter the queryset using the bound value
        """
        if self.value:
            qs = qs.filter(**{self.field_name: self.value})
        return qs


class Filter(BaseFilter):
    """
    Base filter with arbitrary text matching
    """

    choices: Optional[ChoicesType] = None
    _choices: Optional[ChoicesType] = None

    def __init__(
        self,
        param: str,
        field_name: Optional[str] = None,
        label: Optional[str] = None,
        choices: Optional[ChoicesType] = None,
    ):
        super().__init__(param=param, field_name=field_name, label=label)
        if choices is not None:
            self.choices = choices

    def deconstruct(self) -> Dict[str, Any]:
        """
        Deconstruct choices
        """
        kwargs = super().deconstruct()

        if self.choices is not None:
            kwargs["choices"] = copy.copy(self.choices)

        return kwargs

    def set_value(self, value: str):
        """
        Clean a value and store it
        """
        choices = self.get_choices()
        lookup = dict(choices)
        if value not in lookup.keys():
            if self.ignore_invalid:
                value = ""
            else:
                raise FilterError(f"Invalid value for filter {self.label}")

        self.value = value

    def get_context(self) -> Dict["str", Any]:
        context = super().get_context()
        context["choices"] = self._generate_choices_with_urls()
        return context

    def get_choices(self) -> ChoicesType:
        """
        Get choices for use in validation and template rendering

        This should be an iterable of (value, label) tuples, where the value must be a
        unique string, ready to be used in the URL.
        """
        # Check for cache
        if self._choices is not None:
            return self._choices

        # Check for option set in filter constructor
        if self.choices is not None:
            self._choices = self.choices
            return self._choices

        # Look up from db
        if isinstance(
            self.model_field,
            (
                models.OneToOneField,
                models.ForeignKey,
                models.ManyToOneRel,
                models.ManyToManyField,
            ),
        ):
            # Relationship to another model, get all potential values from there
            choices = self.get_related_choices()

        else:
            # Values from this model
            choices = self.get_local_choices()

        self._choices = [self.get_all_choice()] + choices
        return self._choices

    def get_local_choices(self) -> ChoicesType:
        """
        Get choices from the values of the field on this model
        """
        vals = (
            self.model.objects.values_list(self.field_name, flat=True)
            .distinct()
            .order_by(self.field_name)
        )
        choices = [(str(val), str(val)) for val in vals]
        return choices

    def get_related_choices(self) -> ChoicesType:
        """
        Return a queryset of the related model for use by get_choices
        """
        qs = self.get_related_queryset()
        choices = [(str(obj.pk), str(obj)) for obj in qs]
        return choices

    def get_related_queryset(self) -> models.QuerySet:
        related_model = self.model_field.related_model
        qs = related_model.objects.all()
        return qs

    def _generate_choices_with_urls(self):
        """
        Template choice generator

        Called by get_context

        Returns tuples of::

            (value, label, url, selected)
        """
        if not self.view:
            raise FilterError(f"Filter {self.label} has no view, incorrect usage")
        if not hasattr(self.view, "request"):
            raise FilterError(f"Filter {self.label} view has no request")

        choices = self.get_choices()

        request = self.view.request
        base_url = request.path
        params = request.GET.copy()

        for value, label in choices:
            if not value:
                # Delete from params. Use pop instead of del as we'll also cover the
                # case where no param has been passed
                params.pop(self.param, None)
            else:
                params[self.param] = value

            selected = value == self.value

            yield (value, label, f"{base_url}?{params.urlencode()}", selected)


def str_to_date_tuple(value: str) -> Tuple[Optional[int], Optional[int]]:
    """
    The value as a (year, month) tuple, where year/month is either an int or None

    Years are only valid if they're between 1000 and 3000. This should cover all
    common use cases; if you need dates outside this range, implement a custom
    filter.
    """
    if not value:
        return None, None

    parts = value.split("-")
    year_raw: str = parts[0]
    year: Optional[int]
    try:
        year = int(year_raw)
    except ValueError:
        year = None

    # If a value was passed, the first part must be a valid year
    if year is None or year < 1000 or year > 3000:
        raise FilterError("Invalid date")

    month: Optional[int] = None
    if len(parts) > 1:
        month_raw: str = parts[1]
        try:
            month = int(month_raw)
        except ValueError:
            month = None

        # If there was a valid year and a dash, it muts be followed by a valid month
        if month is None or month < 1 or month > 12:
            raise FilterError("Invalid date")

    return year, month


class DateHierarchyFilter(Filter):
    """
    Filter by date hierarchy - list years, then list months within a selected year

    ``filter.value`` is the raw value from the querystring, ``""``, ``yyyy`` or
    ``yyyy-mm``

    ``filter.year`` and ``filter.month`` are ``None`` or the integer values
    """

    year: Optional[int] = None
    month: Optional[int] = None

    template_name = "fastview/filters/date_hierarchy.html"

    def set_value(self, value: str):
        """
        Clean a value and store it
        """
        # Store the raw string value
        self.value = value

        # Validate and store the year/month
        try:
            year, month = str_to_date_tuple(value)
        except FilterError as e:
            raise FilterError(f"{e} for filter {self.label}")

        self.year = year
        self.month = month

    def get_choices(self):
        if isinstance(self.model_field, models.DateTimeField):
            date_method = "datetimes"
        elif isinstance(self.model_field, models.DateField):
            date_method = "dates"
        else:
            raise FilterError(
                "Date filter can only be applied to a DateField or DateTimeField"
            )

        if self.year is None:
            # No date specified
            qs = self.model.objects
            # qs.dates() or qs.datetimes()
            dates = getattr(qs, date_method)(self.field_name, "year")
            return [(str(date.year), str(date.year)) for date in dates]

        # Year specified
        qs = self.model.objects.filter(**{f"{self.field_name}__year": self.year})
        # qs.dates() or qs.datetimes()
        dates = getattr(qs, date_method)(self.field_name, "month")
        choices: ChoicesType = [
            ("", _("All")),
        ]
        choices += [
            (f"{self.year}-{date.strftime('%m')}", date.strftime("%B"))
            for date in dates
        ]
        return choices

    def get_context(self):
        context = super().get_context()
        context.update(
            {
                "year": self.year,
            }
        )
        return context

    def process(self, qs: models.QuerySet) -> models.QuerySet:
        if self.year is None:
            # No date specified, no filter
            return qs

        if self.month is None:
            # Year specified, no month
            qs = qs.filter(**{f"{self.field_name}__year": self.year})

        else:
            # Year and month specified
            qs = qs.filter(
                **{
                    f"{self.field_name}__year": self.year,
                    f"{self.field_name}__month": self.month,
                }
            )

        return qs


class BooleanFilter(Filter):
    """
    Filter a boolean yes/no field

    ``filter.value`` is the raw value from the querystring, ``""``, ``1`` or ``0``

    ``filter.boolean`` is the boolean value, ``None``, ``True`` or ``False``
    """

    boolean: Optional[bool]
    choices = [("", _("All")), ("1", _("Yes")), ("0", _("No"))]

    def set_value(self, value: str):
        """
        Clean a value and store it
        """
        super().set_value(value)
        self.boolean = None
        if self.value == "1":
            self.boolean = True
        if self.value == "0":
            self.boolean = False

    def process(self, qs: models.QuerySet) -> models.QuerySet:
        """
        Filter the queryset using the bound value
        """
        if self.boolean is None:
            return qs

        return qs.filter(**{self.field_name: self.boolean})


class TreeFilter(Filter):
    """
    Tree filter

    Operates on a list of (parent, [child, child, ...]) tuples, where each child is a
    similar tuple. Each parent and child object should be a tuple of (value, label)

    For example::

        [
        ((value, label), [
            ((child_value, label), []), ((child_value, label), [...]),
        ]), ((value, label), []),
    ]
    """

    tree: Optional[TreeListType] = None
    template_name: str = "fastview/filters/tree.html"

    def __init__(
        self,
        param: str,
        field_name: Optional[str] = None,
        label: Optional[str] = None,
        tree: Optional[TreeListType] = None,
    ):
        """
        Take a tree object rather than choices
        """
        super().__init__(
            param=param,
            field_name=field_name,
            label=label,
        )
        self.tree = tree

    def get_context(self) -> Dict["str", Any]:
        context: Dict["str", Any] = super().get_context()
        context["choices"] = self._generate_choices_with_urls()
        context["level"] = 1
        return context

    def get_tree(self) -> TreeListType:
        if self.tree is None:
            raise ValueError(f"Filter {self.label} has no tree")
        return [(self.get_all_choice(), [])] + self.tree

    def set_value(self, value: str):
        """
        Clean a value and store it
        """
        tree: TreeListType = self.get_tree()

        # Check tree for valid value
        stack = tree[:]
        is_valid: bool = False
        choice: ChoiceType
        children: TreeListType
        while stack:
            choice, children = stack.pop(0)
            choice_value, _ = self._choice_to_value_label(choice)
            if choice_value == value:
                is_valid = True
                break

            stack = children + stack

        if not is_valid:
            if self.ignore_invalid:
                value = ""
            else:
                raise FilterError(f"Invalid value for filter {self.label}")

        self.value = value

    def _choice_to_value_label(self, choice) -> Tuple[str, str]:
        return choice

    def _generate_choices_with_urls(self):
        """
        Template choice generator

        Called by get_context

        Returns tuples of::

            (value, label, url, selected, child_selected, children)

        Where children is None, or another generator of the same tuples
        """
        if not self.view:
            raise FilterError(f"Filter {self.label} has no view, incorrect usage")
        if not hasattr(self.view, "request"):
            raise FilterError(f"Filter {self.label} view has no request")

        tree: TreeListType = self.get_tree()

        request = self.view.request
        base_url = request.path
        params = request.GET.copy()

        def generate_for_nodelist(nodes):
            choice: ChoiceType
            children: TreeListType

            for choice, children in nodes:
                value, label = self._choice_to_value_label(choice)

                if not value:
                    # Delete from params. Use pop instead of del as we'll also cover the
                    # case where no param has been passed
                    params.pop(self.param, None)
                else:
                    params[self.param] = value

                selected = self.value == value
                child_selected = self.value.startswith(f"{value}/")

                yield (
                    value,
                    label,
                    f"{base_url}?{params.urlencode()}",
                    selected,
                    child_selected,
                    generate_for_nodelist(children) if children else None,
                )

        yield from generate_for_nodelist(tree)


field_lookup = {
    models.DateField: DateHierarchyFilter,
    models.DateTimeField: DateHierarchyFilter,
    models.BooleanField: BooleanFilter,
}


def field_to_filter_class(field: models.Field) -> Type[Filter]:
    """
    Return the most appropriate filter for the given a model field
    """
    field_cls = type(field)
    filter_cls = field_lookup.get(field_cls, Filter)
    return filter_cls

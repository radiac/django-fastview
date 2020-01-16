"""
Mixins for fastviews
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, List, Optional, Type, Union

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ImproperlyConfigured
from django.db.models import AutoField, Model
from django.urls import reverse
from django.utils.translation import gettext as _

from ..constants import INDEX_VIEW
from ..forms import InlineParentModelForm
from ..permissions import Denied, Permission
from .display import AttributeValue, DisplayValue
from .objects import AnnotatedObject


if TYPE_CHECKING:
    from ..viewgroup import ViewGroup
    from .inlines import Inline


class FastViewMixin(UserPassesTestMixin):
    """
    Mixin for class-based views to support FastView groups

    Controls permission-based access.

    Attributes:
        title: Pattern for page title (added to context as ``title``). Will be rendered
            by ``format``; can use ``{action}`` to show the action label. Subclasses
            will provide additional values for formatting.
        viewgroup: Reference to the ViewGroup this view is called by (if any).
        action: The viewgroup action. Used for template name.
        action_label: Label when linking to this action. Defaults to view name.
        permission: A Permission class instance
        has_id_slug: Used to determine whether to insert an id (pk or slug) into the url
            or not.

    .. _UserPassesTestMixin:
        https://docs.djangoproject.com/en/2.2/topics/auth/default/#django.contrib.auth.mixins.UserPassesTestMixin
    """

    title: str = "{action}"
    viewgroup: Optional[ViewGroup] = None
    # TODO: action is now only used for templates; rename to more appropriate var
    action: Optional[str] = None
    action_label: Optional[str] = None
    permission: Permission = Denied()
    has_id_slug: bool = False

    def get_test_func(self) -> Callable:
        """
        Tells the base class ``UserPassesTestMixin`` to call ``self.has_permission`` to
        see if the user has access.
        """
        return self.has_permission

    def has_permission(self) -> bool:
        """
        Check for permission to see this view based on ``self.permission``

        Returns:
            Whether or not the user has permission to see this view
        """
        if not self.permission:
            return True

        return self.permission.check(self.request)

    def get_template_names(self) -> List[str]:
        # Get default template names
        names = super().get_template_names()
        extra = []

        # Look for a viewgroup action template
        if self.viewgroup:
            extra.append(f"{self.viewgroup.get_template_root()}/{self.action}.html")

        # Add in our default as a fallback
        extra.append(self.default_template_name)
        return names + extra

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Make the title available
        context["title"] = self.get_title()

        # Let the viewgroup extend the context
        if self.viewgroup:
            context.update(self.viewgroup.get_context_data(self))

        return context

    def get_title(self):
        """
        Get the title for the page

        Used by the default templates
        """
        return self.title.format(**self.get_title_kwargs())

    def get_title_kwargs(self, **kwargs):
        kwargs["action"] = self.action.replace("_", " ").title()
        return kwargs

    @classmethod
    def get_action_label(cls):
        """
        Get the action label for this view

        Can be called on class or instance
        """
        if cls.action_label:
            return cls.action_label
        name = getattr(cls, "__name__", type(cls).__name__)
        if name.endswith("View"):
            name = name[:-4]
        return name.replace("_", " ").title()


class ModelFastViewMixin(FastViewMixin):
    """
    Mixin for class-based views which act on models
    """

    model: Type[Model]
    annotated_model_object = None
    action_links = None

    def get_queryset(self):
        """
        Filter the queryset using the class filter and permissions
        """
        qs = super().get_queryset()
        if self.permission:
            qs = self.permission.filter(self.request, qs)
        return qs

    def get_annotated_model_object(self):
        """
        Return an AnnotatedObject class for the annotated_object_list
        """
        return AnnotatedObject.for_view(self, action_links=self.get_action_links())

    def get_title_kwargs(self, **kwargs):
        """
        Get keywords for the ``self.title`` format string
        """
        kwargs = super().get_title_kwargs(**kwargs)
        kwargs.update(
            {
                "verbose_name": self.model._meta.verbose_name.title(),
                "verbose_name_plural": self.model._meta.verbose_name_plural.title(),
            }
        )
        return kwargs

    def get_action_links(self):
        """
        Return list of action links

        Default template will use this to show links to object action views

        If ``self.action_links is None``, all available action links will be shown
        """
        return self.action_links


class ObjectFastViewMixin(ModelFastViewMixin):
    """
    Mixin for class-based views which operate on a single object
    """

    def has_permission(self) -> bool:
        if not self.permission:
            return True

        # TODO: The permission check is carried out before ``self.get()`` sets
        # ``self.object``, so we need to get it ourselves. This adds a call to
        # ``get_object()``; this should be cached so not result in any additional db
        # requests, but still seems unnecessary. Either rewimplement super's get to
        # check for ``self.object``, or patch Django to do the same - see Django #18849
        instance = None
        if self.has_id_slug:
            instance = self.get_object()
        return self.permission.check(self.request, self.model, instance)

    def get_title_kwargs(self, **kwargs):
        kwargs = super().get_title_kwargs(**kwargs)
        kwargs["object"] = str(self.object)
        return kwargs


class BaseFieldMixin:
    """
    For views with a fields attribute

    Generate fields based on the model

    For use with a view using SingleObjetMixin or MultipleObjectMixin
    """

    model: Model  # Help type hinting to identify the intended base classes
    fields: List[Any]  # Liskov made me do it

    def __init__(self, *args, **kwargs):
        """
        Default self.fields to the fields defined on the model
        """
        super().__init__(*args, **kwargs)

        exclude = getattr(self, "exclude", [])

        if getattr(self, "fields", None):
            if exclude:
                raise ValueError("Cannot specify both fields and exclude")
        else:
            # Follow Django admin rules - anything not an AutoField with editable=True
            self.fields = [
                field.name
                for field in self.model._meta.get_fields()
                if not isinstance(field, AutoField)
                and field.editable is True
                and field.name not in exclude
            ]

        self.exclude = exclude


class FormFieldMixin(BaseFieldMixin):
    fields: List[str]
    exclude: List[str]


class InlineMixin:
    """
    Mixin for form CBVs (subclassing ProcessFormView) which support inlines
    """

    # TODO: Consider merging with FormFieldMixin when adding support for nested inlines
    model: Model  # Help type hinting to identify the intended base classes
    get_form_kwargs: Callable  # Help type hinting
    inlines: Optional[List[Inline]] = None

    def get_form(self, form_class=None):
        """
        Return a InlineParentModelForm
        """
        # Get form instance and ensure it's an InlineParentModelForm
        form = super().get_form(form_class)
        if not isinstance(form, InlineParentModelForm):
            # It's not. It should have been set by .inlines.Inline, but someone must
            # have overriden the default without knowing what they're doing. Fix it.
            orig_cls = form.__class__
            form.__class__ = type(
                str("InlineParent%s" % orig_cls.__name__),
                (InlineParentModelForm, orig_cls),
                {},
            )
            form.__init_inlines__()

        # Look up and register the formsets
        form_prefix = self.get_prefix()
        if self.inlines is not None:
            for index, inline_cls in enumerate(self.inlines):
                inline = inline_cls(self.model)
                formset_cls = inline.get_formset()
                # TODO: Watch for annotated object modifying self.object
                kwargs = self.get_formset_kwargs(
                    inline, prefix=f"{form_prefix}__formset_{index}"
                )
                formset = formset_cls(**kwargs)
                form.add_formset(formset)

        return form

    def get_formset_kwargs(self, inline: Inline, **extra_kwargs):
        kwargs = self.get_form_kwargs()
        kwargs.update(extra_kwargs)
        kwargs["initial"] = inline.get_initial(self)
        return kwargs


class DisplayFieldMixin(BaseFieldMixin):
    """
    For views which display field values

    Ensure all fields are DisplayValue instances
    """

    fields: List[Union[str, DisplayValue]]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        display_values: List[DisplayValue] = []
        field_names = [field.name for field in self.model._meta.get_fields()]

        for field in self.fields:
            if not isinstance(field, DisplayValue):
                if field not in field_names:
                    raise ValueError(f'Unknown field "{field}"')
                field = AttributeValue(field)
            display_values.append(field)
        self.fields = display_values

    @property
    def labels(self):
        """
        Return labels for the fields
        """
        return [field.get_label(self) for field in self.fields]


class SuccessUrlMixin(SuccessMessageMixin):
    """
    For views which have a success url
    """

    success_message = _("%(model_name)s was saved successfully")

    def get_success_url(self):
        try:
            return super().get_success_url()
        except ImproperlyConfigured:
            if self.viewgroup:
                return reverse(f"{self.request.resolver_match.namespace}:{INDEX_VIEW}")
            raise

    def get_success_message(self, cleaned_data):
        data = cleaned_data.copy()
        if hasattr(self, "model"):
            data["model_name"] = self.model._meta.verbose_name.title()
        return self.success_message % data

"""
Mixins for fastviews
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Type, Union, cast

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ImproperlyConfigured
from django.db.models import AutoField, Model
from django.urls import reverse
from django.utils.translation import gettext as _

from ..constants import INDEX_VIEW, TEMPLATE_FRAGMENT_SLUG
from ..forms import InlineParentModelForm
from ..permissions import Denied, Permission
from .display import AttributeValue, DisplayValue
from .objects import AnnotatedObject


if TYPE_CHECKING:
    from ..viewgroups import ViewGroup
    from .inlines import Inline


class AbstractFastView(UserPassesTestMixin):
    """
    Mixin for a class-based view which supports FastView groups but does not render a
    template
    """

    viewgroup: Optional[ViewGroup] = None
    permission: Optional[Permission] = None
    has_id_slug: bool = False

    @classmethod
    def config(cls, **attrs: Dict[str, Any]) -> AbstractFastView:
        """
        Creates a new subclass of this View, with the attributes provided
        """
        # Collect attrs from the view and its bases
        base_attrs = {}
        mro = cls.mro()
        mro.reverse()
        for base_cls in mro:
            base_attrs.update(vars(base_cls))

        # Create a subclass of the original view with the new attributes
        # cast because type inference can't tell we'll subclassing ourselves
        view = cast(AbstractFastView, type(cls.__name__, (cls,), attrs))
        return view

    def get_test_func(self) -> Callable:
        """
        Tells the base class ``UserPassesTestMixin`` to call ``self.has_permission`` to
        see if the user has access.
        """
        return self.has_permission

    @classmethod
    def get_permission(cls) -> Permission:
        """
        Check for permission to see this view

        If no ``permission`` attribute is defined on this view or its base classes, it
        will check the ``permission`` attribute of its ``viewgroup``. If that is not
        set, the permission check will default to ``False``, preventing access.

        Returns:
            Whether or not the user has permission to see this view
        """
        # Default to no access
        permission: Permission = Denied()

        # Try our permission
        if cls.permission:
            permission = cls.permission

        # Fall back to viewgroup's permission
        elif cls.viewgroup and hasattr(cls.viewgroup, "permission"):
            # Collect viewgroup permission, or Denied if the viewgroup has set
            # permission=None to remove an inherited permission
            permission = cls.viewgroup.permission or permission

        return permission

    def has_permission(self) -> bool:
        """
        Check if this view instance has permission, based on self.request
        """
        permission = self.__class__.get_permission()
        return permission.check(self.request)


class FastViewMixin(AbstractFastView):
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
    # TODO: action is name it's registered on viewgroup; rename to more appropriate var
    action: Optional[str] = None
    action_label: Optional[str] = None

    _as_fragment = False
    fragment_template_name = None

    def dispatch(self, request, *args, as_fragment=False, **kwargs):
        self._as_fragment = as_fragment
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self) -> List[str]:
        # Get default template names
        names = super().get_template_names()
        extra = []

        # Look for a viewgroup action template
        if self.viewgroup:
            root = self.viewgroup.get_template_root()
            if root:
                extra.append(f"{root}/{self.action}.html")

        # Add in our default as a fallback
        extra.append(self.default_template_name)

        names += extra
        if not self._as_fragment:
            return names

        # Convert to use fragment templates
        fragment_names = []
        if self.fragment_template_name is not None:
            fragment_names = [self.templatetag_template_name]

        for name in names:
            parts = name.split("/")
            name = "/".join(parts[:-1] + [TEMPLATE_FRAGMENT_SLUG, parts[-1]])
            fragment_names.append(name)

        return fragment_names

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

        Used by the default templates.

        The dict returned by :meth:`get_title_kwargs` is applied to :attr:`title` using
        format.
        """
        return self.title.format(**self.get_title_kwargs())

    def get_title_kwargs(self, **kwargs):
        """
        Return a dict for generating a page title in :meth:`get_title`:

        ``action``
            The name of this view's action, eg list, update, delete
        """
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
        """
        Check if this view instance has permission, based on self.request, the model and
        the model instance
        """
        permission = self.__class__.get_permission()

        # TODO: The permission check is carried out before ``self.get()`` sets
        # ``self.object``, so we need to get it ourselves. This adds a call to
        # ``get_object()``; this should be cached so not result in any additional db
        # requests, but still seems unnecessary. Either rewimplement super's get to
        # check for ``self.object``, or patch Django to do the same - see Django #18849
        instance = None
        if self.has_id_slug:
            instance = self.get_object()
        return permission.check(self.request, self.model, instance)

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
    fields: Optional[List[Any]] = None  # Liskov made me do it
    exclude: Optional[List[Any]] = None

    def get_fields(self):
        """
        Return either self.fields, or all editable fields on the model
        (excluding anything in self.exclude)
        """
        fields = self.fields
        if fields is None:
            # Fields not specified
            exclude = self.exclude or []

            # Follow Django admin rules - anything not an AutoField with editable=True
            fields = [
                field.name
                for field in self.model._meta.get_fields()
                if not isinstance(field, AutoField)
                and field.editable is True
                and field.name not in exclude
            ]

        elif self.exclude is not None:
            raise ImproperlyConfigured(
                "Specifying both 'fields' and 'exclude' is not permitted."
            )

        return fields


class FormFieldMixin(BaseFieldMixin):
    def get_form_class(self):
        self.fields = self.get_fields()
        return super().get_form_class()


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

    # Caches
    _displayvalues: List[DisplayValue] = None
    _displayvalue_lookup: Dict[str, DisplayValue] = None

    def resolve_displayvalue_slug(self, slug):
        """
        Resolve a DisplayValue slug to its DisplayValue object
        """
        # Ensure cache is populated
        if self._displayvalue_lookup is None:
            fields = self.get_fields()
            self._displayvalue_lookup = {
                field.get_slug(view=self): field for field in fields
            }

        if slug not in self._displayvalue_lookup:
            raise ValueError(f"Invalid order field {slug}")

        return self._displayvalue_lookup[slug]

    def get_fields(self):
        """
        Return a list of DisplayValue fields
        """
        if self._displayvalues is not None:
            return self._displayvalues

        # Get the list of fields - may be a mix of field names and DisplayValues
        fields = super().get_fields()

        # Prepare
        display_values: List[DisplayValue] = []
        field_names = [field.name for field in self.model._meta.get_fields()]

        # Convert field names to DisplayValue instances, and build slug lookup table
        for field in fields:
            if not isinstance(field, DisplayValue):
                # Passed something that's not a DisplayValue - decide what to do

                if (
                    field in field_names  # It's a straight field value
                    or hasattr(self.model, field)  # model attribute, probably a method
                    # TODO: Support attributes added by the queryset, eg aggregations
                ):
                    field = AttributeValue(field)
                else:
                    raise ValueError(f'Unknown field "{field}"')
            display_values.append(field)

        self._displayvalues = display_values
        return display_values

    @property
    def labels(self):
        """
        Return labels for the fields
        """
        return [field.get_label(self) for field in self.get_fields()]


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

from __future__ import annotations

from inspect import isclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type

from django.core.exceptions import FieldDoesNotExist
from django.urls import include, path, reverse
from django.views.generic import View
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import MultipleObjectMixin

from ..constants import INDEX_VIEW, OBJECT_VIEW, VIEW_SUFFIX
from ..permissions import Permission
from ..views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from ..views.mixins import AbstractFastView


if TYPE_CHECKING:
    from django.db.models.base import ModelBase
    from django.urls.resolvers import CheckURLMixin


class ViewGroupType(type):
    def __new__(cls, name, bases, dct):
        """
        Resolve view configuration dicts into View.config() responses

        This cannot easily be done from ViewGroup._collect_views, as at that point we'd
        have to manually navigate the MRO and keep applying config dicts as we find
        them. This way we can just look at the immediate bases
        """
        for attr, view in dct.items():
            # Collect view name from attr
            if not attr.endswith(VIEW_SUFFIX):
                continue

            name = attr[: -len(VIEW_SUFFIX)]

            if isinstance(view, dict):
                # We've found a config, look for the view class defined on a base class
                config = view
                base_view = None
                for base in bases:
                    base_view = getattr(base, attr, None)
                    if not isinstance(base_view, AbstractFastView):
                        continue

                # Unexpected, most likely dev mistake, raise an error
                if not base_view:
                    raise AttributeError(
                        f"View config dict found at {name}.{attr}, "
                        "but no base classes declare a FastView with that name"
                    )

                # Reconfigure the view we found
                dct[attr] = base_view.config(**config)

        return super().__new__(cls, name, bases, dct)


class ViewGroup(metaclass=ViewGroupType):
    """
    Collection of related views served from the same root url
    """

    # Template root path
    template_root: Optional[str] = None

    # Base template name for view templates to extend
    base_template_name: str = "fastview/base.html"

    # Permission to apply to all views (overridden by view-specific permissions)
    permission: Optional[Permission]

    # All groups must define an index view
    index_view: Type[AbstractFastView]

    views: Dict[str, AbstractFastView]

    action_links: Optional[List[str]] = None

    def __init__(self, **kwargs):
        """
        Configure view group
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

        self._collect_views()

    def get_template_root(self) -> Optional[str]:
        """
        Root path for templates for this view group
        """
        return self.template_root

    def _collect_views(self) -> None:
        """
        Build a dict of all views defined on this group.

        Intended for internal use, can only be called once; see ``self.views`` instead.

        The ViewGroup will use ``_get_view_attrs()`` to collect attributes to set on the
        View class. To avoid changing the view itself (in case it is used elsewhere), it
        will be subclassed before being modified.

        This approach is used instead of ``view.as_view(**attrs)`` because that would
        create a new View instance, but a ViewGroup may need to interrogate a view's
        class attributes before instantiation.
        """
        if getattr(self, "views", None) is not None:
            raise RuntimeError("Views can only be collected once")
        self.views = {}

        # Extract views defined on the class
        for attr in dir(self):
            # Collect view name from attr
            if not attr.endswith(VIEW_SUFFIX):
                continue
            name = attr[: -len(VIEW_SUFFIX)]
            view = getattr(self, attr)

            # If it's a view, reconfigure and store
            if isclass(view) and issubclass(view, AbstractFastView):
                config = self._get_view_attrs(name, view)
                self.views[name] = view.config(**config)
                setattr(self, attr, self.views[name])

    def _get_view_attrs(self, name: str, view: View) -> Dict[str, Any]:
        """
        Get a dict of attrs to set on a view class before it is added to self.views
        """
        return {
            "viewgroup": self,
            "action": name,
        }

    def include(self, namespace=None):
        """
        Call to insert ViewGroup into urls

        Example:

            urlpatterns = [
                url(r'^mygroup/', MyGroup().include(namespace="mygroup")),
            ]

        If called as a classmethod, will automatically instantiate itself
        """

        # https://stackoverflow.com/questions/28237955/same-name-for-classmethod-and-instancemethod

        # Build response that urlpatterns expects
        urls = self.get_urls()
        # TODO: pick up app namespace from originating app
        if namespace is None:
            return include(urls)
        app_namespace = "fastview"
        return include((urls, app_namespace), namespace=namespace)

    def get_urls(self) -> List[CheckURLMixin]:
        """
        Collect or build url patterns for each view
        """
        patterns = []
        name: str
        view: Type[View]
        for name, view in self.views.items():
            # Build pattern
            pattern: CheckURLMixin = self.get_url_pattern_for_view(name, view)
            patterns.append(pattern)
        return patterns

    def get_url_pattern_for_view(self, name: str, view: Type[View]) -> CheckURLMixin:
        """
        Get the URL pattern for the given view name and view

        Subclasses will probably want to override `get_url_route_for_view()` instead
        """
        # Build route string
        route = self.get_url_route_for_view(name, view)

        # Resolve view
        pattern_view = view.as_view()

        # Build the pattern
        pattern = path(route, pattern_view, name=name)
        return pattern

    def get_url_route_for_view(self, name: str, view: Type[View]) -> str:
        """
        Build the URL pattern match for the given view name and view.

        Called internally by `get_url_pattern_for_view()` has checked for `get_<name>_url()`.
        """
        if name == INDEX_VIEW:
            route = ""
        else:
            route = f"{name}/"
        return route

    def get_action_links(self):
        return self.action_links

    def get_context_data(self, view: View, **context: Any) -> Dict[str, Any]:
        """
        Get additional context data for the view
        """
        # Build using delayed closures, avoid unnecessary potentially expensive lookups
        # TODO: Is this really worth the complexity? Candidate for simplification.
        def can_factory(to_view):
            def can():
                permission = to_view.get_permission()
                return permission.check(view.request)

            return can

        def get_url_factory(name):
            def get_url():
                return reverse(f"{view.request.resolver_match.namespace}:{name}")

            return get_url

        def action_links_factory(action_link_data):
            def action_links():
                return [
                    (label, get_url())
                    for name, label, can, get_url in action_link_data
                    if can()
                ]

            return action_links

        action_links = self.get_action_links()
        action_link_data = []
        for name, to_view in self.get_basic_views().items():
            can = can_factory(to_view)
            get_url = get_url_factory(name)

            context[f"can_{name}"] = can
            context[f"get_{name}_url"] = get_url

            if (action_links is None or name in action_links) and name != view.action:
                action_link_data.append(
                    (name, to_view.get_action_label(), can, get_url)
                )

        if action_links:
            action_link_data = sorted(
                action_link_data, key=lambda data: action_links.index(data[0])
            )

        context["view"] = view
        context["action_links"] = action_links_factory(action_link_data)

        if context.get("base_template_name") is None:
            context["base_template_name"] = self.base_template_name

        return context

    def get_object_views(self):
        """
        Return a filtered list of views which operate on an existing object - views
        which have the attribute ``has_id_slug == True`` (see mixins)
        """
        return {
            name: view
            for name, view in self.views.items()
            if getattr(view, "has_id_slug", False)
        }

    def get_basic_views(self):
        """
        Return a filtered list of views which do not operate on an existing object - all
        views which are not returned by ``get_object_views``
        """
        return {
            name: view
            for name, view in self.views.items()
            if not getattr(view, "has_id_slug", False)
        }


class ModelViewGroup(ViewGroup):
    # TODO: Move all of this into the base ViewGroup, except ``action_links`` and views
    model: Type[ModelBase]
    id_field_name = "pk"
    owner_field_name = None
    action_links = ["index", "create", "update", "delete"]

    index_view: Type[AbstractFastView] = ListView
    detail_view: Type[AbstractFastView] = DetailView
    create_view: Optional[Type[AbstractFastView]] = CreateView
    update_view: Optional[Type[AbstractFastView]] = UpdateView
    delete_view: Optional[Type[AbstractFastView]] = DeleteView

    def _get_view_attrs(self, name: str, view: View) -> Dict[str, Any]:
        """
        Add model-specific attributes to the view
        """
        attrs = super()._get_view_attrs(name, view)

        # Only add the model if one hasn't been defined already - a group may contain
        # views which operate on different models
        if (
            issubclass(view, (SingleObjectMixin, MultipleObjectMixin))
            and view.model is None
        ):
            attrs["model"] = self.model

        # Propagate action links, unless specified on the view
        if getattr(view, "action_links", None) is None:
            attrs["action_links"] = self.get_action_links()

        return attrs

    def get_template_root(self):
        template_root = super().get_template_root()
        if template_root:
            return template_root
        app_label, model_name = self.model._meta.label_lower.split(".", 1)
        return f"{app_label}/{model_name}"

    def get_url_route_for_view(self, name: str, view: Type[View]) -> CheckURLMixin:
        """
        Build the URL route including the object's primary key or slug
        """
        if view.has_id_slug:
            # TODO: add slug support
            if name == OBJECT_VIEW:
                return "<int:pk>/"
            else:
                return f"<int:pk>/{name}/"

        elif name == OBJECT_VIEW:
            raise ValueError("Detail view must be a SingleObjectMixin subclass")

        return super().get_url_route_for_view(name, view)

    def get_id_field(self):
        """
        Return the field to identify the model instance by
        """
        # TODO: Do we need this?
        if self.id_field_name is not None:
            return self.model._meta.get_field(self.id_field_name)

        try:
            field = self.model._meta.get_field("slug")
        except FieldDoesNotExist:
            field = None

        if not field or not field.unique:
            field = self.model._meta.pk

        return field

    def get_owner_field(self):
        """
        Return the field to identify the model instance owner by
        """
        if self.owner_field_name is not None:
            return self.model._meta.get_field(self.owner_field_name)

        try:
            field = self.model._meta.get_field("owner")
        except FieldDoesNotExist:
            raise FieldDoesNotExist("Cannot find owner field")
        return field

from __future__ import annotations

from inspect import isclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type

from django.core.exceptions import FieldDoesNotExist
from django.urls import include, path, reverse
from django.views.generic import View
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import MultipleObjectMixin

from .constants import INDEX_VIEW, OBJECT_VIEW, VIEW_SUFFIX
from .permissions import Permission
from .views import CreateView, DeleteView, DetailView, ListView, UpdateView


if TYPE_CHECKING:
    from django.db.models import Model
    from django.urls.resolvers import CheckURLMixin


class ViewGroup:
    """
    Collection of related views served from the same root url
    """

    # Template root path
    template_root: Optional[str] = None

    # Permissions definition, passed on to the views
    permissions: Optional[Dict[str, Permission]]

    # All groups must define an index view
    index_view: Type[View]

    views: Dict[str, Type[View]]

    action_links: Optional[List[str]] = None

    def __init__(self, **kwargs):
        """
        Configure view group
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

        self._collect_views()

    def get_template_root(self) -> str:
        return self.template_root or ""

    def _collect_views(self) -> None:
        """
        Build a dict of all views defined on this group.

        Intended for internal use, can only be called once; see ``self.views`` instead.

        The ViewGroup will use ``_get_view_attrs()`` to collect attributes to set on the
        View class. To avoid changing the view itself (in case it is used elsewhere), it
        will be subclassed before being modified.

        This approach is used instead of ``view.as_view(**attrs)`` because a ViewGroup
        needs to interrogate its views' class attributes before instantiation.
        """
        if getattr(self, "views", None) is not None:
            raise RuntimeError("Views can only be collected once")
        self.views = {}

        # Perform initial checks of permissions to make sure they are all permissions
        if self.permissions:
            invalid_perms = list(
                filter(
                    lambda pair: not isinstance(pair[1], Permission),
                    self.permissions.items(),
                )
            )
            if invalid_perms:
                raise ValueError(
                    "Permissions must be a subclass of"
                    f" Permission: {', '.join([p[0] for p in invalid_perms])}"
                )

        # Extract views defined on the class
        for attr in dir(self):
            # Collect view name from attr
            if not attr.endswith(VIEW_SUFFIX):
                continue
            name = attr[: -len(VIEW_SUFFIX)]

            # Check and store the view
            view = getattr(self, attr)
            if isclass(view) and issubclass(view, View):
                # Add attributes as necessary
                attrs = self._get_view_attrs(name, view)
                if attrs:
                    view = type(view.__name__, (view,), attrs)
                    setattr(self, f"{name}{VIEW_SUFFIX}", view)

                # Store
                self.views[name] = view
            else:
                # Not a view
                continue

        # Sanity check the permissions to avoid typos
        if self.permissions:
            invalid_names = set(self.permissions.keys()).difference(
                set(self.views.keys())
            )
            if invalid_names:
                raise ValueError(
                    f"Permissions defined without views: {', '.join(invalid_names)}"
                )

    def _get_view_attrs(self, name: str, view: View, **attrs: Any) -> Dict[str, Any]:
        """
        Get a dict of attrs to set on a view class before it is added to self.views
        """
        attrs.update({"viewgroup": self, "action": name})

        if self.permissions:
            permission = self.permissions.get(name)
        else:
            permission = None
        if getattr(view, "permission", None) != permission:
            attrs["permission"] = permission
        return attrs

    def include(self, namespace):
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

        Called internally by `get_url_for_view()` has checked for `get_<name>_url()`.
        """
        if name == INDEX_VIEW:
            route = ""
        else:
            route = f"{name}/"
        return route

    def get_action_links(self):
        return self.action_links

    def get_context_data(self, view: View, **context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get additional context data for the view
        """
        # Build using delayed closures, avoid unnecessary potentially expensive lookups
        # TODO: Is this really worth the complexity? Candidate for simplification.
        def can_factory(to_view):
            def can():
                return to_view.permission.check(view.request)

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

        context["action_links"] = action_links_factory(action_link_data)

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
    model: Model
    id_field_name = "pk"
    owner_field_name = None
    action_links = ["index", "create", "update", "delete"]

    index_view: Type[View] = ListView
    detail_view: Type[View] = DetailView
    create_view: Optional[Type[View]] = CreateView
    update_view: Optional[Type[View]] = UpdateView
    delete_view: Optional[Type[View]] = DeleteView

    def _get_view_attrs(self, name: str, view: View, **attrs: Any) -> Dict[str, Any]:
        """
        Add model-specific attributes to the view
        """
        attrs = super()._get_view_attrs(name, view, **attrs)

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
            return
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

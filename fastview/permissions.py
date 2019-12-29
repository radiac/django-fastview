"""
Permissions for views
"""
from __future__ import annotations

from typing import Optional, Type

from django.db.models import Model, Q, QuerySet
from django.http import HttpRequest


Q_ALL = Q(pk__isnull=False)
Q_NONE = Q(pk__isnull=True)


class Permission:
    """
    Base permission class - permission denied
    """

    def check(
        self,
        request: HttpRequest,
        model: Optional[Type[Model]] = None,
        instance: Optional[Model] = None,
    ) -> bool:
        """
        See if the user is allowed to access the view

        Arguments:
            request: The request we're checking
            instance: Model instance, if checking for access to a model
        """
        return False

    def filter(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        """
        Filter a queryset based on the check for this class

        Subclasses should override ``filter_q`` instead to allow binary operations.

        Arguments:
            request: The request we're checking
            queryset: The queryset to filter

        Returns:
            queryset: If the check passes, returns the full queryset, otherwise returns
                an empty queryset
        """
        q = self.filter_q(request, queryset)
        return queryset.filter(q)

    def filter_q(self, request: HttpRequest, queryset: QuerySet) -> Q:
        """
        Return a Q object for ``self.filter``
        """
        # TODO: Optimise this by removing these from the query; at worst we make the
        # query less complicated, at best we end up returning qs.none() or qs.all()
        if self.check(request):
            # Allow all
            return Q_ALL

        # Allow none
        return Q_NONE

    def __and__(self, other: Permission) -> Permission:
        return AndPermission(self, other)

    def __or__(self, other: Permission) -> Permission:
        return OrPermission(self, other)

    def __invert__(self) -> Permission:
        return NotPermission(self)


class Denied(Permission):
    pass


class OrPermission(Permission):
    """
    OR two permissions - either left or right
    """

    left: Permission
    right: Permission

    def __init__(self, left: Permission, right: Permission):
        self.left = left
        self.right = right

    def check(
        self,
        request: HttpRequest,
        model: Optional[Type[Model]] = None,
        instance: Optional[Model] = None,
    ) -> bool:
        """
        Allows if either check passes
        """
        can_left = self.left.check(request, model, instance)
        can_right = self.right.check(request, model, instance)
        return can_left or can_right

    def filter_q(self, request: HttpRequest, queryset: QuerySet) -> Q:
        """
        Returns a Q object of the OR of the two permission filters
        """
        left_q = self.left.filter_q(request, queryset)
        right_q = self.right.filter_q(request, queryset)
        return left_q | right_q


class AndPermission(Permission):
    """
    AND two permissions - only if left and right
    """

    left: Permission
    right: Permission

    def __init__(self, left: Permission, right: Permission):
        self.left = left
        self.right = right

    def check(
        self,
        request: HttpRequest,
        model: Optional[Type[Model]] = None,
        instance: Optional[Model] = None,
    ) -> bool:
        """
        Allows if either check passes
        """
        can_left = self.left.check(request, model, instance)
        can_right = self.right.check(request, model, instance)
        return can_left and can_right

    def filter_q(self, request: HttpRequest, queryset: QuerySet) -> Q:
        """
        Returns a Q object of the AND of the two permission filters
        """
        left_q = self.left.filter_q(request, queryset)
        right_q = self.right.filter_q(request, queryset)
        return left_q & right_q


class NotPermission(Permission):
    """
    NOT a permission
    """

    permission: Permission

    def __init__(self, permission: Permission):
        self.permission = permission

    def check(
        self,
        request: HttpRequest,
        model: Optional[Type[Model]] = None,
        instance: Optional[Model] = None,
    ) -> bool:
        """
        Invert the check - allow if it fails, deny if it passes
        """
        if self.permission.check(request, model, instance):
            return False
        return True

    def filter_q(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        """
        Invert the filter - exclude anything matched from the returned queryset
        """
        q = self.permission.filter_q(request, queryset)
        return ~q


class Public(Permission):
    """
    Public permission - everyone can access
    """

    def check(
        self,
        request: HttpRequest,
        model: Optional[Type[Model]] = None,
        instance: Optional[Model] = None,
    ) -> bool:
        return True


class Login(Permission):
    """
    Users must be logged in
    """

    def check(
        self,
        request: HttpRequest,
        model: Optional[Type[Model]] = None,
        instance: Optional[Model] = None,
    ) -> bool:
        if request.user.is_authenticated:
            return True
        return False


class Staff(Permission):
    """
    User must be staff
    """

    def check(
        self,
        request: HttpRequest,
        model: Optional[Type[Model]] = None,
        instance: Optional[Model] = None,
    ) -> bool:
        return request.user.is_staff


class Superuser(Permission):
    """
    User must be superuser
    """

    def check(
        self,
        request: HttpRequest,
        model: Optional[Type[Model]] = None,
        instance: Optional[Model] = None,
    ) -> bool:
        return request.user.is_superuser


class Django(Permission):
    """
    Django-based permissions

    Example::

        class Edit(ChangeView):
            model = MyModel
            permission = Django('change')

    equivalent to::

        request.user.has_perm('myapp.change_mymodel')
    """

    action: str

    def __init__(self, action: str):
        """
        Django permission needs to know which permission it's looking for

        Arguments:
            action: maps to the permissions registered with Django's permissions system;
                by default one of ``add``, ``change``, ``delete`` or ``view``
        """
        self.action = action
        super().__init__()

    def check(
        self,
        request: HttpRequest,
        model: Optional[Type[Model]] = None,
        instance: Optional[Model] = None,
    ) -> bool:
        if not model:
            if instance:
                model = type(instance)
            else:
                return False
        app_label, model_name = model._meta.label_lower.split(".", 1)
        if request.user.has_perm(f"{app_label}.{self.action}_{model_name}"):
            return True
        return False

    def filter_q(self, request: HttpRequest, queryset: QuerySet) -> Q:
        if self.check(request, model=queryset.model):
            # Allow all
            return Q_ALL
        # Allow none
        return Q_NONE


class Owner(Permission):
    """
    User must own the model object
    """

    owner_field: str

    def __init__(self, owner_field: str):
        """
        The Owner permission requires additional arguments on instantiation.

        Arguments:
            owner_field: The name of the field on the model which is a foreign key to
                the user who owns the object.

        Anonymous (unauthenticated) users will always fail
        """
        self.owner_field = owner_field
        super().__init__()

    def check(
        self,
        request: HttpRequest,
        model: Optional[Type[Model]] = None,
        instance: Optional[Model] = None,
    ) -> bool:
        if not instance or not request.user.is_authenticated:
            return False
        owner_id = getattr(instance, f"{self.owner_field}_id")
        if owner_id == request.user.pk:
            return True
        return False

    def filter_q(self, request: HttpRequest, queryset: QuerySet) -> Q:
        if request.user.is_authenticated:
            return Q(**{self.owner_field: request.user})
        return Q_NONE

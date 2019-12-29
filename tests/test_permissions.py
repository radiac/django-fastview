"""
Test fastview/permissions.py
"""
import pytest

from fastview.permissions import Django, Login, Owner, Public, Staff, Superuser

from .app.models import Entry


def test_public__public_can_access(test_data, request_public):
    perm = Public()
    assert perm.check(request_public) is True
    assert perm.filter(request_public, test_data).count() == test_data.count()


def test_login__public_cannot_access(test_data, request_public):
    perm = Login()
    assert perm.check(request_public) is False
    assert perm.filter(request_public, test_data).count() == 0


def test_login__authed_can_access(test_data, request_owner):
    perm = Login()
    assert perm.check(request_owner) is True
    assert perm.filter(request_owner, test_data).count() == test_data.count()


def test_staff__public_cannot_access(test_data, request_public):
    perm = Staff()
    assert perm.check(request_public) is False
    assert perm.filter(request_public, test_data).count() == 0


def test_staff__authed_cannot_access(test_data, request_owner):
    perm = Staff()
    assert perm.check(request_owner) is False
    assert perm.filter(request_owner, test_data).count() == 0


def test_staff__staff_can_access(test_data, request_staff):
    perm = Staff()
    assert perm.check(request_staff) is True
    assert perm.filter(request_staff, test_data).count() == test_data.count()


def test_superuser__public_cannot_access(test_data, request_public):
    perm = Superuser()
    assert perm.check(request_public) is False
    assert perm.filter(request_public, test_data).count() == 0


def test_superuser__authed_cannot_access(test_data, request_owner):
    perm = Superuser()
    assert perm.check(request_owner) is False
    assert perm.filter(request_owner, test_data).count() == 0


def test_superuser__staff_cannot_access(test_data, request_staff):
    perm = Superuser()
    assert perm.check(request_staff) is False
    assert perm.filter(request_staff, test_data).count() == 0


def test_superuser__superuser_can_access(test_data, request_superuser):
    perm = Superuser()
    assert perm.check(request_superuser) is True
    assert perm.filter(request_superuser, test_data).count() == test_data.count()


def test_django__public_cannot_access(test_data, request_public):
    perm = Django(action="add")
    assert perm.check(request_public, model=Entry) is False
    assert perm.filter(request_public, test_data).count() == 0


def test_django__authed_cannot_access(test_data, request_owner):
    perm = Django(action="add")
    assert perm.check(request_owner, model=Entry) is False
    assert perm.filter(request_owner, test_data).count() == 0


def test_django__staff_cannot_access(test_data, request_staff):
    perm = Django(action="add")
    assert perm.check(request_staff, model=Entry) is False
    assert perm.filter(request_staff, test_data).count() == 0


def test_django__superuser_can_access(test_data, request_superuser):
    perm = Django(action="add")
    assert perm.check(request_superuser, model=Entry) is True
    assert perm.filter(request_superuser, test_data).count() == test_data.count()


@pytest.mark.django_db
def test_django__user_with_permission_can_access(
    test_data, request_other, user_other, add_entry_permission
):
    user_other.user_permissions.add(add_entry_permission)
    perm = Django(action="add")
    assert perm.check(request_other, model=Entry) is True
    assert perm.filter(request_other, test_data).count() == test_data.count()


def test_owner__public_cannot_access(test_data, request_public):
    perm = Owner(owner_field="author")
    # Test data is ordered, the first is owned by user_owner
    owned = test_data.first()
    assert perm.check(request_public, instance=owned) is False
    assert perm.filter(request_public, test_data).count() == 0


def test_owner__owner_can_access_theirs(test_data, request_owner, user_owner):
    perm = Owner(owner_field="author")
    owned = test_data.first()
    assert perm.check(request_owner, instance=owned) is True
    assert perm.filter(request_owner, test_data).count() == 2
    assert perm.filter(request_owner, test_data).filter(author=user_owner).count() == 2


def test_owner__other_can_access_theirs(test_data, request_other, user_other):
    perm = Owner(owner_field="author")
    owned = test_data.first()
    assert perm.check(request_other, instance=owned) is False
    assert perm.filter(request_other, test_data).count() == 2
    assert perm.filter(request_other, test_data).filter(author=user_other).count() == 2


def test_owner__staff_cannot_access(test_data, request_staff):
    perm = Owner(owner_field="author")
    owned = test_data.first()
    assert perm.check(request_staff, instance=owned) is False
    assert perm.filter(request_staff, test_data).count() == 0


def test_owner__superuser_cannot_access(test_data, request_superuser):
    perm = Owner(owner_field="author")
    owned = test_data.first()
    assert perm.check(request_superuser, instance=owned) is False
    assert perm.filter(request_superuser, test_data).count() == 0


def test_and__owner_and_staff__owner_cannot_access(test_data, request_owner):
    perm = Owner(owner_field="author") & Staff()
    owned = test_data.first()
    assert perm.check(request_owner, instance=owned) is False
    assert perm.filter(request_owner, test_data).count() == 0


def test_and__owner_and_staff__staff_cannot_access(test_data, request_staff):
    perm = Owner(owner_field="author") & Staff()
    owned = test_data.first()
    assert perm.check(request_staff, instance=owned) is False
    assert perm.filter(request_staff, test_data).count() == 0


def test_and__owner_and_staff__staff_owner_can_access(
    test_data, request_owner, user_owner
):
    perm = Owner(owner_field="author") & Staff()
    owned = test_data.first()
    user_owner.is_staff = True
    user_owner.save()
    assert perm.check(request_owner, instance=owned) is True
    assert perm.filter(request_owner, test_data).count() == 2


def test_or__owner_or_staff__owner_can_access(test_data, request_owner):
    perm = Owner(owner_field="author") | Staff()
    owned = test_data.first()
    assert perm.check(request_owner, instance=owned) is True
    assert perm.filter(request_owner, test_data).count() == 2


def test_or__owner_or_staff__staff_can_access(test_data, request_staff):
    perm = Owner(owner_field="author") | Staff()
    owned = test_data.first()
    assert perm.check(request_staff, instance=owned) is True
    assert perm.filter(request_staff, test_data).count() == 4


def test_or__owner_or_staff__staff_owner_can_access(
    test_data, request_owner, user_owner
):
    perm = Owner(owner_field="author") | Staff()
    owned = test_data.first()
    user_owner.is_staff = True
    user_owner.save()
    assert perm.check(request_owner, instance=owned) is True
    assert perm.filter(request_owner, test_data).count() == 4


def test_or__owner_or_staff__other_cannot_access(test_data, request_other, user_other):
    perm = Owner(owner_field="author") | Staff()
    owned = test_data.first()
    assert perm.check(request_other, instance=owned) is False
    assert perm.filter(request_other, test_data).count() == 2
    assert perm.filter(request_other, test_data).filter(author=user_other).count() == 2


def test_not__not_owner__all_can_access_all_except_own(
    test_data, request_owner, user_owner
):
    perm = ~Owner(owner_field="author")
    owned = test_data.first()
    not_owned = test_data.exclude(author=user_owner).first()
    assert perm.check(request_owner, instance=owned) is False
    assert perm.check(request_owner, instance=not_owned) is True
    assert perm.filter(request_owner, test_data).count() == 2
    assert perm.filter(request_owner, test_data).filter(author=user_owner).count() == 0


def test_and_not__staff_not_owner__staff_can_access_all_except_own(
    test_data, request_owner, user_owner
):
    perm = Staff() & ~Owner(owner_field="author")
    owned = test_data.first()
    not_owned = test_data.exclude(author=user_owner).first()
    user_owner.is_staff = True
    user_owner.save()
    assert perm.check(request_owner, instance=owned) is False
    assert perm.check(request_owner, instance=not_owned) is True
    assert perm.filter(request_owner, test_data).count() == 2
    assert perm.filter(request_owner, test_data).filter(author=user_owner).count() == 0

"""
Test viewgroup
"""
from fastview import permissions
from fastview.viewgroups import ModelViewGroup

from .app.models import Entry


def test_modelviewgroup_permissions__permissions_set_on_subclass():
    class TestPermission(permissions.Permission):
        pass

    test_permission = TestPermission()

    class Entries(ModelViewGroup):
        permission = test_permission
        model = Entry

    # Permissions are set at instantiation
    entries = Entries()
    assert entries.index_view.get_permission() == test_permission
    assert entries.detail_view.get_permission() == test_permission
    assert entries.create_view.get_permission() == test_permission
    assert entries.update_view.get_permission() == test_permission
    assert entries.delete_view.get_permission() == test_permission

    # Not at definition
    assert isinstance(Entries.index_view.get_permission(), permissions.Denied)
    assert isinstance(Entries.detail_view.get_permission(), permissions.Denied)
    assert isinstance(Entries.create_view.get_permission(), permissions.Denied)
    assert isinstance(Entries.update_view.get_permission(), permissions.Denied)
    assert isinstance(Entries.delete_view.get_permission(), permissions.Denied)


def test_modelviewgroup_index__index_lists(add_url, client, user_owner):
    class Entries(ModelViewGroup):
        permission = permissions.Public()
        model = Entry

    Entry.objects.create(author=user_owner)
    Entry.objects.create(author=user_owner)

    add_url("", Entries().include(namespace="entries"))
    response = client.get("/")
    assert len(response.context_data["object_list"]) == 2

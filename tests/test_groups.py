"""
Test viewgroup
"""
from fastview import permissions
from fastview.groups import ModelViewGroup

from .app.models import Entry


def test_modelviewgroup_permissions__permissions_set_on_subclass():
    perms = {
        action: type(f"{action.title()}Permission", (permissions.Permission,), {})()
        for action in ("index", "detail", "create", "update", "delete")
    }

    class Entries(ModelViewGroup):
        permissions = perms
        model = Entry

    # Permissions are set at instantiation
    entries = Entries()
    assert entries.index_view.permission == perms["index"]
    assert entries.detail_view.permission == perms["detail"]
    assert entries.create_view.permission == perms["create"]
    assert entries.update_view.permission == perms["update"]
    assert entries.delete_view.permission == perms["delete"]

    # Not at definition
    assert isinstance(Entries.index_view.permission, permissions.Denied)
    assert isinstance(Entries.detail_view.permission, permissions.Denied)
    assert isinstance(Entries.create_view.permission, permissions.Denied)
    assert isinstance(Entries.update_view.permission, permissions.Denied)
    assert isinstance(Entries.delete_view.permission, permissions.Denied)


def test_modelviewgroup_index__index_lists(add_url, client, user_owner):
    perms = {
        action: type(f"{action.title()}Permission", (permissions.Public,), {})()
        for action in ("index", "detail", "create", "update", "delete")
    }

    class Entries(ModelViewGroup):
        permissions = perms
        model = Entry

    Entry.objects.create(author=user_owner)
    Entry.objects.create(author=user_owner)

    add_url("", Entries().include(namespace="entries"))
    response = client.get("/")
    assert len(response.context_data["object_list"]) == 2

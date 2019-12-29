"""
Pytest fixtures
"""
from django.urls import path

import pytest

from .app import urls


# Password for all test users
PASSWORD = "x"


@pytest.fixture
def urlpatterns():
    yield urls.urlpatterns
    urls.urlpatterns.clear()


@pytest.fixture
def add_url(urlpatterns):
    def add_url(pattern, include):
        urlpatterns.append(path(pattern, include))

    return add_url


@pytest.fixture
def user_owner(django_user_model):
    return django_user_model.objects.create(username="owner", password=PASSWORD)


@pytest.fixture
def user_other(django_user_model):
    return django_user_model.objects.create(username="other", password=PASSWORD)


@pytest.fixture
def user_staff(django_user_model):
    return django_user_model.objects.create(
        username="staff", password=PASSWORD, is_staff=True
    )


@pytest.fixture
def user_superuser(django_user_model):
    return django_user_model.objects.create(
        username="superuser", password=PASSWORD, is_staff=True, is_superuser=True
    )


@pytest.fixture
def test_data(db, user_owner, user_other):
    from .app.models import Entry

    Entry.objects.create(title="1", author=user_owner)
    Entry.objects.create(title="2", author=user_owner)
    Entry.objects.create(title="3", author=user_other)
    Entry.objects.create(title="4", author=user_other)

    return Entry.objects.all().order_by("title")


@pytest.fixture
def request_public(rf):
    from django.contrib.auth.models import AnonymousUser

    request = rf.get("/")
    request.user = AnonymousUser()
    return request


@pytest.fixture
def request_owner(rf, user_owner):
    request = rf.get("/")
    request.user = user_owner
    return request


@pytest.fixture
def request_other(rf, user_other):
    request = rf.get("/")
    request.user = user_other
    return request


@pytest.fixture
def request_staff(rf, user_staff):
    request = rf.get("/")
    request.user = user_staff
    return request


@pytest.fixture
def request_superuser(rf, user_superuser):
    request = rf.get("/")
    request.user = user_superuser
    return request


@pytest.fixture
def add_entry_permission():
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    from .app.models import Entry

    content_type = ContentType.objects.get_for_model(Entry)
    permission = Permission.objects.get(content_type=content_type, codename="add_entry")
    return permission

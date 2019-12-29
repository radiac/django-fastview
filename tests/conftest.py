"""
Initialise pytest for django and set up fixtures
"""
import django
from django.conf import settings

from .fixtures import *  # noqa


def pytest_configure():

    settings.configure(
        DEBUG=True,
        DATABASES={
            "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
        },
        SECRET_KEY="secret",
        ROOT_URLCONF="tests.app.urls",
        STATIC_URL="/static/",
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "APP_DIRS": True,
            }
        ],
        MIDDLEWARE_CLASSES=(
            "django.middleware.common.CommonMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
        ),
        INSTALLED_APPS=(
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.sites",
            "django.contrib.staticfiles",
            "fastview",
            "tests.app",
        ),
    )

    django.setup()

===============
Django Fastview
===============

Build admin-style views with minimal code.

.. image:: https://travis-ci.org/radiac/django-fastview.svg?branch=master
    :target: https://travis-ci.org/radiac/django-fastview

.. image:: https://coveralls.io/repos/radiac/django-fastview/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/radiac/django-fastview?branch=master

* Project site: http://radiac.net/projects/django-fastview/
* Source code: https://github.com/radiac/django-fastview
* Requires Python 3.7 or later and Django 2.2 or later


Overview
========

Django admin is great for creating quick CRUD views for admin users, but is not suitable
for end users.

Fastview is inspired by Django admin - write code to manage objects in a few lines,
using groups of standard generic views which can be supplemented, overridden or replaced
as necessary, and styled and tied into the rest of your site.

Fastview adds a layer of access control to make it straightforward to manage who can
access each view, and provides default templates to get you up and running quickly.

It supports inline formsets, with an optional customisable JavaScript library to manage
the UI.

Note: this is an alpha release; expect feature and API changes in future versions. Check
upgrade notes for instructions when upgrading.


Quickstart
==========

Install using pip::

    pip install django-fastview

Add to ``INSTALLED_APPS``::

    INSTALLED_APPS = [
        ...
        "fastview",
    ]

Use view groups to build a set of CRUD views in one go, or use the views independently::

    # views.py
    class BlogViewGroup(ModelViewGroup):
        model = Blog
        publish = MyPublishView  # Django view class
        permissions = {
            "index": Public(),
            "detail": Public(),
            "create": Login(),  # Allow any logged in user to create a post
            "update": Staff() | Owner("owner"),  # Allow staff or post owners to edit
            "delete": Django("delete"),  # Only users with the delete permission
            "publish": Staff() & ~Owner("owner"),  # Staff can publish but not their own
        }

    # urls.py
    urlpatterns = [ # ...
        url(r'^blog/', BlogViewGroup().include(namespace="blog")),
    ]

For more details see the main documentation.

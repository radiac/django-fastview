===============
Django Fastview
===============

Build views to manage model data, with minimal code and lots of features.

.. image:: https://travis-ci.org/radiac/django-fastview.svg?branch=master
    :target: https://travis-ci.org/radiac/django-fastview

.. image:: https://coveralls.io/repos/radiac/django-fastview/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/radiac/django-fastview?branch=master

* Project site: http://radiac.net/projects/django-fastview/
* Source code: https://github.com/radiac/django-fastview
* Requires Python 3.7 or later and Django 2.2 or later


Overview
========

Fastview is like Django admin for your user-facing site:

* quickly create sets of views to manage models (list, read, create, update and delete)
* support for inline formsets
* permission-based access


But it is more flexible and powerful than Django admin:

* uses generic views so it's easy to customise and extend
* has default templates which can be easily customised or replaced
* is easy to style to fit into the rest of your site
* permissions are optional and easy to extend to row-level object checks
* provides fragment support for partial renders in other pages

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

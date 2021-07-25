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


Write a wiki where anyone can view, add, edit and delete pages::

    # urls.py (for example purposes - normally define the viewgroup in app/views.py)
    from fastview.groups import ModelViewGroup
    from fastview.permissions import Public
    from mywiki.models import Wiki


    class WikiViewGroup(ModelViewGroup):
        model = Wiki
        permission = Public()

    urlpatterns = [
        url(r'^wiki/', WikiViewGroup().include(namespace="wiki")),
    ]

This will create a functioning set of list, detail, create, update and delete views
under the ``/wiki/`` path on your site.


Or build a more complex view group with custom view classes and complex access
controls::

    # urls.py (for example purposes)
    from fastview.groups import ModelViewGroup
    from fastview.permissions import Public, Login, Staff, Owner, Django
    from myblog.models import Blog
    from myblog.views import BlogUpdateView, BlogPublishView


    class BlogViewGroup(ModelViewGroup):
        model = Blog

        # Default permission for views - any views without explicit permissions will
        # require that user is logged in
        permission = Login()

        # Make the list view public by reconfiguring it with a call to View.config()
        list_view = fastview.views.generics.ListView.config(
            permission=Public(),
        )

        # Make the detail view public by reconfiguring it with the dict shorthand format
        detail_view = dict(
            permission=Public(),
        )

        # Override update with a custom view, and limit access to staff or post owners
        update_view = BlogUpdateView.config(
            permission=Staff() | Owner("owner"),
        )

        # Use the Django permission framework to manage who can delete Blog objects
        delete_view = dict(
            permission=Django("delete"),
        )

        # Add a publish view where only staff can access, but only if it's not their own
        publish_view = BlogPublishView.config(
            permission=Staff() & ~Owner("owner"),
        )

    urlpatterns = [
        url(r'^blog/', BlogViewGroup().include(namespace="blog")),
    ]

You may then want to create a custom templates at ``templates/myblog/blog/list.html``
``templates/myblog/blog/detail.html``to change the way blog posts are rendered.

For more details see the main documentation.

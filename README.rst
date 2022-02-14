===============
Django Fastview
===============

Flexible view system with built-in HTMX support.

.. image:: https://travis-ci.org/radiac/django-fastview.svg?branch=master
    :target: https://travis-ci.org/radiac/django-fastview

.. image:: https://coveralls.io/repos/radiac/django-fastview/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/radiac/django-fastview?branch=master

.. image:: https://readthedocs.org/projects/django-fastview/badge/?version=latest
    :target: https://django-fastview.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

* Project site: http://radiac.net/projects/django-fastview/
* Documentation: https://django-fastview.readthedocs.io/
* Source code: https://github.com/radiac/django-fastview
* Requires Python 3.7 or later and Django 2.2 or later


Fastview slashes development time for modern hybrid frontends - build comprehensive yet
customisable CRUD views in a couple of lines, with built-in HTMX support.

* Create a view group to manage models - list, read, create, update and delete views
* All views are class-based, so they're quick and easy to customise
* Default templates are designed to be customised or replaced to fit your design
* Advanced permission system allows fine-grained row-level access control
* Built-in support for HTMX, inline model formsets and more

Note: this is an alpha release; expect feature and API changes in future versions. Check
upgrade notes for instructions when upgrading.


Example
=======

Lets write a wiki where anyone can view, add, edit and delete pages::

    # urls.py (for example purposes - normally define the viewgroup in app/views.py)
    from fastview.viewgroups import ModelViewGroup
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

There are all sorts of things you can do from here:

* The views are all based on Django's generic class-based views, so they're easy to
customise



Quickstart
==========

1. Install using pip::

    pip install django-fastview

2. Add to ``INSTALLED_APPS``::

    INSTALLED_APPS = [
        ...
        "fastview",
    ]

3. Optional: add the default JavaScript and CSS to your templates or frontend build
   process.


See Getting Started in the documentation for more details.



Advanced example
----------------

Build a more complex view group with custom view classes and complex access controls::

    # urls.py (for example purposes)
    from fastview.viewgroups import ModelViewGroup
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


More examples
-------------

See Examples in the documentation for more details on these two examples, as well as how
you can use fastview to:

* configure and customise the views
* use permissions to control access to individual database objects
* add inline models to your forms
* and more

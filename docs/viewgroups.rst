===========
View groups
===========

A view group is a collection of views which know about each other and are added to the
site urls as one.


.. _viewgroups.viewgroup:

``ViewGroup``
=============

A base class which defines no views.

To define a view on a viewgroup, assign it to the group class as ``<action>_view``. One
view must be defined as the index action. For example::

    from fastview import ViewGroup

    class MyViews(ViewGroup):
        index_view = ListView


.. _viewgroups.modelviewgroup:

``ModelViewGroup``
==================

Defines a viewgroup which operates on a single model (and its related models via
inlines).

Set the ``model`` attribute on the group definition::

    from fastview import ModelViewGroup

    class BlogViews(ModelViewGroup):
        model = Blog

It provides the following view actions:

* ``index``: a list view of all objects
* ``detail``: show an individual object
* ``create``, ``update``, ``delete``: manage the objects

These will default to permission ``Disabled``.


.. _viewgroups.authviewgroup

``AuthViewGroup``
=================

Defines a viewgroup to provide a set of the standard Django auth views, with default
templates.

Usage::

    from fastview.viewgroups.auth import AuthViewGroup

    urlpatterns = [
        path("accounts/", AuthViewGroup().include()),
        ...
    ]


Configuring views
=================

View settings can be overridden in three ways:

Subclassing the view is the most long-winded, but most flexible::

    from fastview.views.generic import ListView

    class BlogList(ListView):
        paginate_by = 10

    class BlogViews(ModelViewGroup):
        model = Blog
        index_view = BlogList


To simplify this, Fastview generic views have a ``.config()`` method to set attributes::

    from fastview.views.generic import ListView

    class BlogViews(ModelViewGroup):
        model = Blog
        index_view = ListView.config(paginate_by=10)


If you don't want to import the view class, you can also configure viewgroup views with
a dict::

    class BlogViews(ModelViewGroup):
        model = Blog
        index_view = dict(paginate_by=10)

(You can also define the dict with the more conventional ``{"paginate_by": 10}`` syntax)

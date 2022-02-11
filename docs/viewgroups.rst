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


Configuring views
=================

=========
Upgrading
=========

For an overview of what has changed between versions, see the :ref:`changelog`.


Instructions
============

1. Check which version of Fastview you are upgrading from::

    python
    >>> import fastview
    >>> fastview.__version__

2. Upgrade the Fastview package::

    pip install --upgrade django-fastview

3. Find your version below and work your way up this document until you've upgraded to
   the latest version


.. _upgrade_0-0-3:

Upgrading from 0.0.3
====================

Permissions
-----------

Viewgroup ``permissions`` are now managed through ``View.config`` and the dict shortcut.

For example, change the old permission dict::

    class BlogViewGroup(ModelViewGroup):
        permissions = {
            "index": Public(),
            "detail": Public(),
        }

to an explicit ``.config()`` call, or a shortcut view configuration dict::

    class BlogViewGroup(ModelViewGroup):
        index_view = views.ListView.config(permission=Public())
        detail_view = dict(permission=Public())

They can still be set directly as ``permission`` on class definitions.

See :ref:`permissions` for more details.


.. _upgrade_0-0-1:

Upgrading from 0.0.1
====================

No changes required


.. _changelog:


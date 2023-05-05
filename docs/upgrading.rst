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


.. _upgrade_0.1.0:

Upgrading from 0.1.0
====================

Template fragments
------------------

Any elements in the full page templates ``fastview/<action>.html`` have been moved into
their fragments; they now just wrap ``fragments/<action>.html`` with a base template.

The included template components in ``includes/<action>/`` have been moved into
``fragments/<action>/``.

Fragment templates have been broken into additional components in ``fragments/action/``
for ease of customisation.

If you were overriding a section of a fragment template in ``fragments/``, or an include
in ``includes/``, you will want to move those changes into the appropriate files in
``fragments/<action>/``

For example, for ``fragments/list.html``:

* the filter was in ``includes/list/filter.html``; it is now in
  ``fragments/list/filter.html``
* the data table was in ``fragments/list.html``; it is now in ``fragments/list/data.html``

There is now a ``{% fragment_component <component> %}`` template tag which honours
template searching logic - eg anywhere it will look for ``fragments/template.html``, it
will look for components in ``fragments/template/``.



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


Imports
-------

The internal structure of Fastview's modules has changed:

* Renamed ``fastview.groups`` to ``fastview.viewgroups``

* Renamed ``fastview.views.generics`` to ``fastview.views.generic``


.. _upgrade_0-0-1:

Upgrading from 0.0.1
====================

No changes required


.. _changelog:


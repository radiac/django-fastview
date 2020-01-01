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


.. _upgrade_0-0-1:

Upgrading from 0.0.1
--------------------

No changes required


.. _changelog:

Changelog
=========

Releases which require special steps when upgrading to them will be marked with
links to the instructions above.

Changes for upcoming releases will be listed without a release date - these
are available by installing the master branch from github (see
:ref:`installation_instructions` for details).


0.0.2, 2020-01-01
-----------------

Adds action link control for default templates

Feature:

* ``ModelViewGroup.action_links`` - define which actions should be linked to in the
  default templates. Can be ignored if using custom templates.
* ``AnnotatedObject.action_links`` - returns a list of ``(label, url)`` tuples for
  ``action_links`` which link to object views
* FastView template contexts have ``action_links`` - a list of ``(label, url)`` tuples
  for linking to basic (non-object) views

Internal:

* ``ModelViewGroup`` has ``get_object_views()`` and ``get_basic_views()`` to split the
  list of views based on the ``FastViewMixin.has_id_slug`` flag


0.0.1, 2019-12-30
-----------------

Initial release

Feature:

* View groups and basic generic views, with template lookup and permissions.

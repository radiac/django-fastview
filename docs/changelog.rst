=========
Changelog
=========

Releases which require special steps when upgrading to them will be marked with
links to the instructions above.

Changes for upcoming releases will be listed without a release date - these
are available by installing the master branch from github (see
:ref:`installation_instructions` for details).


0.1.0, 2022-08-15
-----------------

Feature:

* Support for list view filtering, ordering and searching
* Ability to embed fastviews as fragments in other pages
* Support for list view pagination with standard ``paginate_by`` attribute
* Added ``AuthViewGroup`` for convenient Django auth views
* Improved template defaults and customisation options

Changes:

* Permissions and other view overrides are now managed through View.config()
* Renamed ``fastview.groups`` to ``fastview.viewgroups``
* Renamed ``fastview.views.generics`` to ``fastview.views.generic``
* Removed imports from ``fastview.views``
* Test dependencies have moved from ``setup.cfg`` to ``tests/requirements.txt``


0.0.3, 2020-02-10
-----------------

Adds inline formset support


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

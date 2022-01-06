===============
Getting started
===============

Installation
============

Install using pip::

    pip install django-fastview

Add to ``INSTALLED_APPS``::

    INSTALLED_APPS = [
        ...
        "fastview",
    ]


Usage
=====

Using generic views
-------------------

Fastview defines a set of generic views - subclasses of the Django generic views with a
bit more functionality.

All Fastview views have the following additional attributes:

* ``title = "view title"`` - used for templates
* ``permission = Permission()`` - used to control access - see :ref:`permissions`
* template names default to ``fastview/<action>.html`` - eg ``Create``'s default
  template is ``fastview/create.html``. Override as normal by setting ``template_name``.

Fastview defines 5 generic views:

* ``fastview.views.ListView``

  * ``fields`` supports strings and ``DisplayValue`` instances - see `display fields`_
  * the template has ``annotated_objects``, a list of ``AnnotatedObject`` instances -
    see `annotated objects`_
  * it can have ``filters`` - see `filters`_

* ``fastview.views.DetailView``

  * ``fields`` supports strings and ``DisplayValue`` instances - see `display fields`_
  * the template has ``annotated_object``, an ``AnnotatedObject`` instance -
    see `annotated objects`_

* ``fastview.views.CreateView``

  * Sets a default ``fields`` using all fields on the model (excluding any ``AutoField``
    or model fields with ``editable=False``)

* ``fastview.views.UpdateView``

  * Sets a default ``fields`` using all fields on the model (excluding any ``AutoField``
    or model fields with ``editable=False``)

* ``fastview.views.DeleteView``

  * Provides a default template


View groups
-----------

A view group is a collection of views which know about each other and are added to the
site urls as one.


``ViewGroup``
:::::::::::::

A base class which defines no views.

To define a view on a viewgroup, assign it to the group class as ``<action>_view``. One
view must be defined as the index action. For example::

    from fastview import ViewGroup

    class MyViews(ViewGroup):
        index_view = ListView


``ModelViewGroup``
::::::::::::::::::

Defines a viewgroup which operates on a model.

Set the ``model`` attribute on the group definition::

    from fastview import ModelViewGroup

    class BlogViews(ModelViewGroup):
        model = Blog

It provides the following view actions:

* ``index``: a list view of all objects
* ``detail``: show an individual object
* ``create``, ``update``, ``delete``: manage the objects

These will default to permission ``Disabled``.


Writing custom views
--------------------

To use a custom view in a ``ViewGroup``, your view shold subclass
``fastview.views.FastViewMixin``, or ``fastview.views.ModelFastViewMixin`` for views
which operate on a model.




.. _display fields:

Display fields
--------------

The list and detail views have an enhanced ``fields`` attribute.

* The list view defaults to just show the object string; set it to ``None`` to show all
  fields
* The default view defaults to show all fields
* The ``fields`` attribute is normally a list of strings for the field names
* Enhanced display fields also support a ``DisplayValue`` instance

Fastview provides the following ``DisplayValue`` types:

* ``AttributeValue`` - show an attribute of the object. The following are equivalent::

      fields = ["name"]
      fields = [AttributeValue("name")]

  An ``AttributeValue`` can also take a label, eg
  ``AttributeValue("user", label="Name")``

* ``ObjectValue`` - convert the object to a string using ``str(object)``

Create a custom display value by subclassing one of those or the base ``DisplayValue``
class.


.. _annotated objects:

Annotated objects
-----------------

Fastview uses annotated objects to provide additional functionality and syntactic sugar
when building templates.

An ``AnnotatedObject`` is accessed in the template as ``annotated_object``, or in a list
view as objects in the list ``annotated_objects``.

It has the following attributes:

* ``original`` - reference to the original object
* ``labels`` - list of field labels
* ``values`` - list of field values (same order as ``labels``)
* ``items`` - list of ``(label, value)`` pairs

When used in a viewgroup, it also has object-based permission checks:

* ``can_<action>`` - returns ``True`` or ``False`` based on user permissions.
* ``get_<action>_url`` - returns the URL to the action.

For example::

    {% if annotated_object.can_delete %}
      <a href="{{ annotated_object.get_delete_url }}">Delete</a>
    {% endif %}

Note: in a future release, the ``object`` and ``object_list`` context values will be
replaced by the annotated objects, and the ``annotated_object`` context values will be
deprecated then removed.


Templates
---------

In addition to the annotated object permissions and urls, Fastview sets values in the
context.

Permission checks for views which aren't object-based:

* ``can_<action>`` - returns ``True`` or ``False`` based on user permissions.
* ``get_<action>_url`` - url to the group action

For example::

    {% if can_add %}
      <a href="{{ get_add_url }}">Add</a>
    {% endif %}


Inlines
=======

The ``CreateView`` and ``UpdateView`` support an ``inlines = [...]`` attribute. This
should be a list of ``fastview.Inline`` objects.

For example::

    from fastview import CreateView, Inline

    class CommentInline(Inline):
        model = Comment

    class EntryCreate(CreateView):
        model = Entry
        inlines = [Comment]

The ``Inline`` class looks for attributes which map to Django's
``inlineformset_factory``; to set the number of extra forms for example::

    class CommentInline(Inline):
        model = Comment
        extra = 10

There is a :doc:`JavaScript <javascript>` library to dynamically add and remove forms
from the formset.


Filters
=======

The ``ListView`` supports ``filters = [...]`` attribute. This can be a list of model
field names or ``Filter`` instances.

Fastview has 3 built-in filters:

* ``Filter``: a choice-based filter. Choices can either be specified on the constructor,
  on a subclass, or collected from the model field the filter is acting on. Subclasses
  can also define their own ``get_choices()`` method to override the default behaviour.

* ``DateHierarchyFilter``: lists active years for the DateField or DateTimeField, and
  then when a year is selected, filters by that year and lists active months to drill
  down to.

* ``BooleanFilter``: Yes/No filter for a BooleanField

If you specify the name of the field in the ``filters`` list, the most appropriate
filter will be chosen for you.

Boolean fields

For example::

    from fastview import ListView
    from fastview.filters import Filter

    class EmptyFilter(Filter):
        choices = (
            ('empty': 'Empty'),
            ('set': 'Set'),
        )

        def process(self, qs):
            if self.value == 'empty':
                return qs.filter(**{self.field_name: ''})
            elif self.value == 'set':
                return qs.exclude(**{self.field_name: ''})
            return qs

    class Entries(ListView):
        model = Entry
        filters = ['publish_date', 'is_published', EmptyFilter('title')]

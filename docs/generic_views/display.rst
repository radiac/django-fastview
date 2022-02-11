===============
Display objects
===============

The :doc:`listview` and :doc:`detailview` views have an enhanced ``fields`` attribute.

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


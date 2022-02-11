=================
Annotated objects
=================


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


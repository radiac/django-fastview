=========
Templates
=========

.. _templates__lookup:

Template lookup
===============

All templated Fastview generic views look for templates in the same way:

#.  Viewgroup specific - ``<viewgroup template root>/<view action>.html``

    For a ``ModelViewGroup`` the template root is ``<app label>/<model name>`` in lower
    case.

    Example: for the ``detail`` view for a ``ModelViewGroup`` operating on the
    ``polls.Poll`` model, this template would be ``polls/poll/detail.html``

#.  Fastview default - ``fastview/<view default template name>.html``

    Fastview generic views have a ``default_template_name`` attribute, which is the name
    of the generic view.

    Example: for the ``ListView`` generic view, this template would be
    ``fastview/list.html``

#.  Standard Django generic view ``get_template_name()`` logic

    This will start by looking at the ``template_name`` attribute.

    Certain Django template mixins then have rules for calculating template names, eg
    see `the docs`__ for ``SingleObjectTemplateResponseMixin``.

    __ https://docs.djangoproject.com/en/dev/ref/class-based-views/mixins-single-object/#django.views.generic.detail.SingleObjectTemplateResponseMixin


Context
=======

All Fastview views set values in the context.

Permission checks for views which aren't object-based:

* ``can_<action>`` - returns ``True`` or ``False`` based on user permissions.
* ``get_<action>_url`` - url to the group action

For example::

    {% if can_add %}
      <a href="{{ get_add_url }}">Add</a>
    {% endif %}

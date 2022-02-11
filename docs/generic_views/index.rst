=============
Generic views
=============

Fastview defines a set of generic views - subclasses of the Django generic views with a
bit more functionality:

.. toctree::
    :maxdepth: 2

    listview
    detailview
    createview
    updateview
    deleteview


All Fastview views have the following additional attributes:

* ``title = "view title"`` - used for templates
* ``permission = Permission()`` - used to control access - see :ref:`permissions`
* template names default to ``fastview/<action>.html`` - eg ``Create``'s default
  template is ``fastview/create.html``. Override as normal by setting ``template_name``.



.. toctree::
    :maxdepth: 2
    :caption: Configuring the generic views

    annotated
    display
    inlines

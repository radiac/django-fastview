==========
CreateView
==========


* ``fastview.views.CreateView``

  * Sets a default ``fields`` using all fields on the model (excluding any ``AutoField``
    or model fields with ``editable=False``)

Unlike standard generic CreateView, this supports ``fields`` and ``form_class`` both
being defined.

Start ``success_url`` with a colon to refer to another viewgroup view, eg::

    success_url = ":index"
    success_url = ":detail"

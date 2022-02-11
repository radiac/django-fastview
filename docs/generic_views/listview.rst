========
ListView
========


.. autoclass:: fastview.views.generics.ListView
	:members:
	:show-inheritance:


* ``fields`` supports strings and :doc:`display`
* the template has ``annotated_objects``, a list of :doc:`annotated`
* it can have ``filters``


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


Custom filter on a field
------------------------

It can be useful to filter a field by options other than its values.

For example, to allow you to filter an empty ``CharField``::

    from fastview import ListView
    from fastview.views.filters import Filter

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


.. _filters__custom_filter_method:

Custom filter on a method
-------------------------

It can also be useful to filter on values returned from model methods, such as the
``was_published_recently`` field in the :doc:`tutorial <tutorial>`. Because it's a
method not a field, it can't be used to filter a queryset directly, but we can write a
custom filter to do it instead:

.. code-block:: python
    :caption: polls/views.py

    import datetime
    from fastview.views.filters import BooleanFilter

    class RecentlyPublishedFilter(BooleanFilter):
        def process(self, qs):
            if self.boolean is None:
                return qs

            now = timezone.now()
            date_range = {
                "pub_date__gte": now - datetime.timedelta(days=30),
                "pub_date__lte": now,
            }

            if self.boolean is True:
                return qs.filter(**date_range)
            return qs.exclude(**date_range)

    class PollViewGroup(ModelViewGroup):
        # ...
        index_view = {
            # ...
            "filters": ["pub_date", RecentlyPublishedFilter(param="recent")],
        }

There are few things going on here:

* Our filter subclasses ``fastview.views.filters.BooleanFilter``, as that's going to be
  the closest built-in filter to what we need - it lets the user pick yes or no.

* We override the ``process`` method to filter the queryset. ``self.value`` is going
  to be ``True`` or ``False``, or ``None`` if neither is selected.

* We then instantiate our filter class with ``param="recent"``, which tells Fastview the
  key to use in the URL querystring, eg ``/polls/?recent=1`` will make the filter value
  ``True``.

* The instantiated filter class can then be put in the ``filters`` array in the order
  you want the filters to be shown.


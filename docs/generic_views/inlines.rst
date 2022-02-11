=======
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

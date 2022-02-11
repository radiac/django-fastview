=======================================
Writing your first Fastview app, part 4
=======================================

This part of the tutorial will look at permissions, but has not been completed yet.


Add an owner
============

We can customise any view in the same way. Lets customise the create view to attach the
current user to the model as the owner. First we'll add the user to the model:

.. code-block:: python
    :caption: polls/models.py

    from django.conf import settings

    class Question(models.Model):
        # ...
        created_by = models.ForeignKey(
            settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.CASCADE
        )

... update the database:

.. code-block:: bash

    ./manage.py makemigrations
    ./manage.py migrate

... and create a custom ``AddView``:

.. code-block:: python
    :caption: polls/views.py

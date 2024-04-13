===============================
Writing your first Fastview app
===============================

.. toctree::
    :titlesonly:
    :hidden:

    Part 1 - setup <part1>
    Part 2 - customise <part2>
    Part 3 - auth and permissions <part3>


In this tutorial we'll build on the `official Django tutorial`__ and walk you through
building a fully-featured poll app which will consist of a public site where:

__ https://docs.djangoproject.com/en/3.2/intro/tutorial01/

* members of the public can view polls and vote in them
* users can create and administrate their own polls
* staff can administrate all polls


We will assume you've already followed the official tutorial, and have a basic
understanding of `class-based views`__.

__ https://docs.djangoproject.com/en/3.2/topics/class-based-views/


If you want to skip ahead, the completed project is available on github as the Fastview
`example project`__.

__ https://github.com/radiac/django-fastview/tree/develop/example



Prepare your project
====================

We'll assume that you have just finished part 7 of the official tutorial, and have the
polls app in front of you. You have ``django`` installed. You've also given all your
poll templates the base template ``templates/base_site.html`` using a ``content`` block.
We're also going to change ``Question.was_published_recently`` to use the past 30 days.

You can get a copy of this starting point from from
`<https://github.com/radiac/django-tutorial-starter>`_.

If you'd prefer to just read along we'll cover everything as we go. We're starting with
these models:

.. literalinclude:: index__models.py
    :caption: polls/models.py
    :language: python


Add some sample data
====================

Going forward we'll need some data. We want a good spread across years for when we get
to filtering, so lets create some questions, one a week for 150 weeks - starting a year
and a half ago, and running a year and a half into the future.

Either grab the `management command`__ from the Fastview example project, or run the
following code in ``./manage.py shell``:

.. literalinclude:: index__data.py
    :language: python

__ https://raw.githubusercontent.com/radiac/django-fastview/develop/example/polls/management/commands/add_poll_sample.py


Now we're ready to make a start. Lets move on to `part 1 of this tutorial <part1>`_ to
learn how to add Fastview to your project and set up your first view group.

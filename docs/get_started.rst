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

Optional: add the default Fastview JavaScript and CSS to your templates::

    <head>
      ...
      <link rel="stylesheet" type="text/css" href="{% static "fastview/index.css" %}">
      <script src="{% static "fastview/index.js" %} async></script>
    </head>

* There is a corresponding npm module if you'd prefer to build fastview's frontend as
  part of your existing frontend - see :doc:`frontend` for more details. See
  :doc:`templates` for full customisation options.


Your first view group
=====================

Fastview starts with a ``ViewGroup`` - a collection of class-based views which know
about each other. Most of the time you'll want to use a ``ModelViewGroup``, which
automatically defines CRUD views to list, detail, create, update and delete instances of
a specified model, much like a ``ModelAdmin`` in Django's admin site.

To create a view group to operate on a model, subclass ``ModelViewGroup``. Fastview's
permissions system defaults to denying access, so in this example lets give the public
full access::

    from fastview.viewgroups import ModelViewGroup
    from fastview.permissions import Public

    from mywiki.models import Wiki


    class WikiViewGroup(ModelViewGroup):
        model = Wiki
        permission = Public()


Done. Now add your view group to your main ``urls.py``::

    from mywiki.views import WikiViewGroup

    urlpatterns = [
        url(r'^wiki/', WikiViewGroup().include(namespace="wiki")),
    ]

You can now link into the views on your wiki from your template::

    <nav>
        <a href="{% url "wiki:index" %}">Wiki</a>
    </nav>

Behind the scenes, view groups use Django's class-based views (CBV), so they're easy to
customise and extend.


Next topics
===========

* :doc:`viewgroups`
* :doc:`generic_views/index`
* :doc:`custom_views`
* :doc:`permissions`
* :doc:`templates`

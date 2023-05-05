============
Contributing
============

Contributions are welcome, preferably via pull request. Check the github issues and
project :ref:`roadmap <roadmap>` below to see what needs work. Fastview aims to make
common things easy and everything else possible. If you're thinking about adding a new
feature, it's worth opening a new ticket to discuss it first.

When submitting UI changes, please aim to support the latest versions of Chrome, Firefox
and Edge through progressive enhancement.


Roadmap
=======

Planned breaking changes during alpha:

* Replace action definitions with an ``Action`` class (similar to the ``DisplayValue``)
* Restructure default templates for detail and form views
* Improve default CSS styling
* Split formset JavaScript into a separate project

Planned additional features:

* Add viewgroup attribute boosting
* Add ``DisplayValue`` classes for specific model fields
* Optimise permission queries, particularly for ``permissions.Owner``
* Improved slug management by allowing views to define their own URLs
* Add HTMX support for create, update, delete and detail views
* Add ``Filter`` classes for common use cases in model fields
* Extend ``Action`` class to support HTMX-based actions within the list view
* Optional Tailwind-based theme


Installing
==========

The easiest way to work on Fastview is to fork the project on github, then install it to
a virtualenv::

    mkdir django-fastview
    cd django-fastview
    python3.10 -mvenv venv
    source venv/bin/activate
    pip install -e git+git@github.com:USERNAME/django-fastview.git#egg=django-fastview
    pip install -r venv/src/django-fastview/tests/requirements.txt

(replacing ``USERNAME`` with your username).

This will install the testing dependencies too, and you'll find the Fastview source
ready for you to work on in the ``src`` folder of your virtualenv.


.. _js-build-static:

Building JavaScript
===================

.. note::

    When submitting changes to the JavaScript code, please just commit the changes made
    in ``static_src/`` - **do not** commit built JavaScript resources in
    ``fastview/static/``.

The project is set up to build using `nvm`_ and `yvm`_::

    cd src/django-fastview
    nvm use
    yvm use

.. _nvm: https://github.com/creationix/nvm
.. _yvm: https://yvm.js.org/docs/overview

There are three commands::

    npm run watch  # run a webpack dev server for using with HMR
    npm run dev    # dev build
    npm run build  # minimised prod build for distribution


Testing
=======

Contributions which come with unit tests are likely to be merged more quickly. If you're
fixing a problem, ideally you'd have a test which fails and proves the issue, then
passes once your fix is in place.

Use ``pytest`` to run the tests on your current installation::

  cd path/to/django-fastview
  pytest

This will also generate a ``coverage`` HTML report.


Credits
=======

Thanks to all contributors, who are listed in the :doc:`changelog`.

The icons are from Remix Icon, https://remixicon.com/

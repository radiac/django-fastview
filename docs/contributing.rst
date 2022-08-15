============
Contributing
============

Contributions are welcome, preferably via pull request. Check the github issues and
project :ref:`roadmap <roadmap>` to see what needs work. Fastview aims to make common
things easy and everything else possible. If you're thinking about adding a new feature,
it's worth opening a new ticket to discuss whether it's common enough to be suitable for
adding to the project.

When submitting UI changes, please aim to support the latest versions of Chrome, Firefox
and Edge through progressive enhancement.


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

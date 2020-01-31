=====================
Fastview's JavaScript
=====================

When downloaded from PyPI, this package contains pre-bundled JavaScript for managing
formsets. When used normally, these will be included in your static files and the
default templates will load them automatically; there is nothing more for you to do. See
:ref:`js-pre-bundled` below when writing custom templates.

If you want to customise the JavaScript by subclassing, or want to include it in your
own bundle or build process, you can use the corresponding npm package. Both PyPI and
npm releases follow semantic versioning of ``major.minor.patch``; the ``major.minor``
versions will be released in sync, use the latest ``patch`` version available. See
:ref:`js-customising` below when doing this.

The bundle files are excluded from the repository, so if installing from git you will
need to bundle it yourself - see :ref:`js-build-static` for more details.


.. _js-pre-bundled:

Using the pre-bundled static
============================

Load the static resource in your template::

  <script src="{% static "fastview/index.js" %}></script>


Formsets
--------

The pre-bundled JavaScript looks for all formsets on page load. It expects to find the
following ``data-`` attributes on form elements:

* ``data-fastview-formset``

  * Element: the container of the formset.
  * Value: the prefix for the formset

* ``data-fastview-formset-template``

  * Element: the ``formset.empty_form`` template
  * Value: the templated prefix for the formset, ``formset.empty_form.prefix``

* ``data-fastview-formset-form``

  * Element: the form container
  * Value: the prefix for the form
  * There can be more than one of these

See :gitref:`fastview/templates/create.html` for a sample formset.


.. _js-customising:

Customising and bundling your own
=================================

Customising
-----------

The code is designed to be subclassed. Override values and methods to fit your
templates.

You can override the default formset or form classes; these control how the add and
delete buttons are created or managed, how new forms should be inserted, and what
happens when a form is added or deleted.


Bundling
--------

This project uses features from ES2019; you will currently need Babel with the plugin
for class properties::

  npm install --save-dev @babel/plugin-proposal-class-properties

Your ``.babelrc``::

  {
    presets: ['@babel/preset-env'],
    plugins: ['@babel/plugin-proposal-class-properties'],
  }


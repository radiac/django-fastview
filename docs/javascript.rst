=======================
Working with JavaScript
=======================

Fastview provides JavaScript resources to enhance the default templates. They are
pre-bundled in the ``static`` files for the app, or the source is available for you to
override and bundle in your own project's JavaScript.


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


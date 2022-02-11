===========
Permissions
===========


Using permissions
=================

When checking permissions, Fastview will first check the permission defined on the view,
and then the permission on the viewgroup. If neither are set, it defaults to permission
``Denied``.

To override this you can subclass the view and set ``permission`` directly::

    from fastview.permissions import Login

    class NewBlog(CreateView):
        permission = Login()


Or reconfigure the view when defining the ViewGroup::

    class Blog(ViewGroup):
        create_view = CreateView.config(permission=Login())


If you want to reconfigure the base ViewGroup's view for this attribute, you can also
use a dict::

    class Blog(ViewGroup):
        create_view = dict(permission=Login())

        # Equivalent to:
        # create_view = ViewGroup.create_view.config(permission=Login())


You can set the viewgroup permission with the default ``permission``, which will apply
to any view which doesn't have its own permission::

    class Blog(ViewGroup):
        permission = Login()


Built-in permissions
====================

Fastview provides the following permissions:

``Denied()``
------------

Nobody can access. This is the default.


``Public()``
------------

Everyone can access


``Login()``
-----------

The current user must be logged in


``Staff()``
-----------

The current user must be staff


``Superuser()``
---------------

The current user must be a superuser


``Django(action)``
------------------

For model views: use Django's permission framework.

For example, to see if the user has been given the permission ``blog.add_blog`` you
would use::

    class MyView(..):
        permission = Django("add")


``Owner(owner_field)``
----------------------

For model views: user must be the owner of the object

``owner_field``

    specifies the field name referencing the user who owns the instance

For example::

    class Item(models.Model):
        title = models.CharField(max_length=255)
        author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class ItemViewGroup(ViewGroup):
        delete_view = dict(
            permission=Owner("author")
        )

will mean the current user can only delete an ``Item`` if they are set as the
``author``.


Combining permissions
=====================

Permissions can be combined with AND, OR and NOT operators (using the same syntax as
Django ``Q`` objects):

* ``Staff() | Owner("owner")`` - either staff or the owner
* ``Staff() & Owner("owner")`` - only the owner, and only if they are staff
* ``Staff() & ~Owner("owner")`` - staff who are not the owner


Complex permissions which need to be used in several places can be assigned to
variables::

    staff_not_owner = Staff() & ~Owner("owner")

    class Blog(ViewGroup):
        update_view = dict(permission=staff_not_owner)
        delete_view = dict(permission=staff_not_owner)


Writing custom permissions
==========================

To write a custom permission, subclass ``fastview.permissions.Permission`` and implement
your own ``check()`` and ``filter_q()`` methods.

========
Examples
========

Build a more complex view group with custom view classes and complex access controls::

    # urls.py (for example purposes)
    from fastview.viewgroups import ModelViewGroup
    from fastview.permissions import Public, Login, Staff, Owner, Django
    from myblog.models import Blog
    from myblog.views import BlogUpdateView, BlogPublishView


    class BlogViewGroup(ModelViewGroup):
        model = Blog

        # Default permission for views - any views without explicit permissions will
        # require that user is logged in
        permission = Login()

        # Make the list view public by reconfiguring it with a call to View.config()
        list_view = fastview.views.generics.ListView.config(
            permission=Public(),
        )

        # Make the detail view public by reconfiguring it with the dict shorthand format
        detail_view = dict(
            permission=Public(),
        )

        # Override update with a custom view, and limit access to staff or post owners
        update_view = BlogUpdateView.config(
            permission=Staff() | Owner("owner"),
        )

        # Use the Django permission framework to manage who can delete Blog objects
        delete_view = dict(
            permission=Django("delete"),
        )

        # Add a publish view where only staff can access, but only if it's not their own
        publish_view = BlogPublishView.config(
            permission=Staff() & ~Owner("owner"),
        )

    urlpatterns = [
        url(r'^blog/', BlogViewGroup().include(namespace="blog")),
    ]

You may then want to create a custom templates at ``templates/myblog/blog/list.html``
``templates/myblog/blog/detail.html``to change the way blog posts are rendered.

For more details see the main documentation.

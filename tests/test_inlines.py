"""
Test viewgroup
"""
from fastview import permissions
from fastview.forms import InlineParentModelForm
from fastview.views.generics import UpdateView
from fastview.views.inlines import Inline

from .app.models import Comment, Entry


def test_inline_formset__formset_has_data(add_url, client, user_owner):
    class InlineComment(Inline):
        model = Comment

    class UpdateEntry(UpdateView):
        model = Entry
        permission = permissions.Public()
        inlines = [InlineComment]

    entry = Entry.objects.create(author=user_owner)
    comment_1 = Comment.objects.create(entry=entry, message="test 1")
    comment_2 = Comment.objects.create(entry=entry, message="test 2")

    add_url("<int:pk>/", UpdateEntry.as_view())
    response = client.get(f"/{entry.pk}/")

    # Check the two comments are in the formset
    assert "form" in response.context_data
    form = response.context_data["form"]
    assert isinstance(form, InlineParentModelForm)
    assert len(form.formsets) == 1
    formset = form.formsets[0]
    assert len(formset.forms) == 5
    assert formset.forms[0]["id"].value() == comment_1.id
    assert formset.forms[1]["id"].value() == comment_2.id
    assert formset.forms[2]["id"].value() is None
    assert formset.forms[3]["id"].value() is None
    assert formset.forms[4]["id"].value() is None

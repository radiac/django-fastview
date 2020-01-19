"""
Form classes
"""

from typing import List

from django.forms import BaseInlineFormSet, ModelForm
from django.utils.translation import gettext as _


class InlineParentModelForm(ModelForm):
    formsets: List[BaseInlineFormSet]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__init_inlines__()

    def __init_inlines__(self):
        """
        Called by __init__, or call manually if re-typing an existing form instance
        """
        self.formsets = []

    def add_formset(self, formset: BaseInlineFormSet):
        self.formsets.append(formset)

    def is_valid(self):
        """
        Return True if the form and its formsets have no errors, or False otherwise.
        """
        form_valid = super().is_valid()
        for formset in self.formsets:
            formset_valid = formset.is_bound and not any(formset.errors)

            # Form's invalid if the form or fieldset's invalid
            # But still need to check each fieldset so we know which errors to show
            form_valid = form_valid and formset_valid

        return form_valid

    def save(self, commit=True):
        """
        Save this form's self.instance object if commit=True, and then save the inline
        formsets.

        If commit=False, add a save_formsets() method to the form which can be called
        after the instance is saved manually at a later time.
        """
        instance = super().save(commit)
        for formset in self.formsets:
            formset.save(commit=commit)

        return instance


class InlineChildModelForm(ModelForm):
    @property
    def title(self):
        """
        Return a title for this form suitable for display on the page
        """
        if self.instance.pk:
            return str(self.instance)
        model = type(self.instance)
        return _(f"New {model._meta.verbose_name.title()}")

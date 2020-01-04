"""
Form classes
"""

from typing import List, Optional

from django.forms import ModelForm, BaseInlineFormSet


class InlineParentModelForm(ModelForm):
    formsets: Optional[List[BaseInlineFormSet]]

    def add_formset(self, formset: BaseInlineFormSet):
        if not hasattr(self, "formsets"):
            self.formsets = []

        self.formsets.append(formset)

    def is_valid(self):
        """
        Return True if the form and its formsets have no errors, or False otherwise.
        """
        form_valid = super().is_valid()
        formsets = getattr(self, "formsets", None) or []
        for formset in formsets:
            formset_valid = formset.is_bound and not formset.errors

            # Form's invalid if the form or fieldset's invalid
            # But still need to check each fieldset so we know which errors to show
            form_valid = form_valid and formset_valid

        return form_valid

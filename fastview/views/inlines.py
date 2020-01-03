"""
Form view inlines

Mimic Django admin inlines
"""
from typing import Optional, Type

from django.db.models import Model
from django.forms import ModelForm
from django.forms.models import inlineformset_factory

from .mixins import FormFieldMixin


class Inline(FormFieldMixin):
    model: Model
    parent_model: Model
    form: Type[ModelForm] = ModelForm
    extra: int = 3
    max_num: Optional[int] = None

    def __init__(self, parent_model: Model):
        self.parent_model = parent_model
        super().__init__()

    def get_formset(self):
        return inlineformset_factory(
            parent_model=self.parent_model,
            model=self.model,
            form=self.form,
            fields=self.fields,
            extra=self.extra,
            max_num=self.max_num,
            can_delete=True,
        )

"""
Form view inlines

Mimic Django admin inlines
"""
from typing import Any, Dict, Optional, Type

from django.db.models import Model
from django.forms import ModelForm, BaseInlineFormSet
from django.forms.models import inlineformset_factory

from ..forms import InlineParentModelForm
from .mixins import FormFieldMixin, InlineMixin


class Inline(FormFieldMixin):
    model: Model
    parent_model: Model
    form: Type[ModelForm] = InlineParentModelForm
    extra: int = 3
    max_num: Optional[int] = None

    def __init__(self, parent_model: Model):
        self.parent_model = parent_model
        super().__init__()

    def get_formset(self) -> BaseInlineFormSet:
        return inlineformset_factory(
            parent_model=self.parent_model,
            model=self.model,
            form=self.form,
            fields=self.fields,
            extra=self.extra,
            max_num=self.max_num,
            can_delete=True,
        )

    def get_initial(self, view: InlineMixin) -> Dict[str, Any]:
        # TODO
        return {}

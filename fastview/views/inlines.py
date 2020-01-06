"""
Form view inlines

Mimic Django admin inlines
"""
from typing import Any, Dict, Optional, Type

from django.db.models import Model
from django.forms import BaseInlineFormSet, ModelForm
from django.forms.models import inlineformset_factory

from ..forms import InlineChildModelForm
from .mixins import FormFieldMixin, InlineMixin


class InlineFormSet(BaseInlineFormSet):
    @property
    def title(self):
        return self.model._meta.verbose_name_plural.title()


class Inline(FormFieldMixin):
    model: Model
    parent_model: Model
    form: Type[ModelForm] = InlineChildModelForm
    formset: Type[BaseInlineFormSet] = InlineFormSet
    extra: int = 3
    max_num: Optional[int] = None

    def __init__(self, parent_model: Model):
        self.parent_model = parent_model
        super().__init__()

    def get_formset_class(self):
        cls = self.formset
        if not issubclass(cls, InlineFormSet):
            cls = type(
                "InlineFormSet", (InlineFormSet, cls), {}
            )
        return cls

    def get_formset(self) -> BaseInlineFormSet:
        return inlineformset_factory(
            parent_model=self.parent_model,
            model=self.model,
            form=self.form,
            formset=self.get_formset_class(),
            fields=self.fields,
            extra=self.extra,
            max_num=self.max_num,
            can_delete=True,
        )

    def get_initial(self, view: InlineMixin) -> Dict[str, Any]:
        # TODO
        return {}

"""
Form view inlines

Mimic Django admin inlines
"""
from typing import Any, Callable, Dict, List, Optional, Type

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
    fk_name: Optional[str] = None
    extra: int = 3
    min_num: Optional[int] = None
    max_num: Optional[int] = None
    validate_min: bool = False
    validate_max: bool = False
    formfield_callback: Optional[Callable] = None
    field_classes: Optional[Dict[str, Any]] = None
    widgets: Optional[Dict[str, Any]] = None
    localized_fields: Optional[List[str]] = None
    labels: Optional[Dict[str, str]] = None
    help_texts: Optional[Dict[str, str]] = None
    error_messages: Optional[Dict[str, str]] = None
    can_order: bool = False
    can_delete: bool = True

    def __init__(self, parent_model: Model):
        self.parent_model = parent_model
        super().__init__()

    def get_formset_class(self):
        cls = self.formset
        if not issubclass(cls, InlineFormSet):
            cls = type("InlineFormSet", (InlineFormSet, cls), {})
        return cls

    def get_formset(self) -> BaseInlineFormSet:
        return inlineformset_factory(
            parent_model=self.parent_model,
            model=self.model,
            form=self.form,
            formset=self.get_formset_class(),
            fk_name=self.fk_name,
            fields=self.fields,
            exclude=self.exclude,
            extra=self.extra,
            min_num=self.min_num,
            max_num=self.max_num,
            validate_min=self.validate_min,
            validate_max=self.validate_max,
            formfield_callback=self.formfield_callback,
            field_classes=self.field_classes,
            widgets=self.widgets,
            localized_fields=self.localized_fields,
            labels=self.labels,
            help_texts=self.help_texts,
            error_messages=self.error_messages,
            can_order=self.can_order,
            can_delete=self.can_delete,
        )

    def get_initial(self, view: InlineMixin) -> Dict[str, Any]:
        # TODO
        return {}

from django import template
from django.template import TemplateSyntaxError
from django.template.base import token_kwargs
from django.template.response import SimpleTemplateResponse
from django.test import RequestFactory
from django.urls import resolve, reverse
from django.utils.safestring import mark_safe


register = template.Library()


@register.filter
def formset_pk_name(formset):
    return formset.model._meta.pk.name


@register.tag
def fragment(parser, token):
    """
    Render a fragment view

    Usage::

        {% fragment "view_name" %}
        {% fragment "view_name" positional_arg keyword=arg ? param=value %}

    """
    bits = token.split_contents()
    tag_name = bits.pop(0)
    if len(bits) < 1:
        raise template.TemplateSyntaxError(
            f"{tag_name} tag requires at least one argument"
        )

    view_name = parser.compile_filter(bits.pop(0))
    args = []
    kwargs = {}
    params = {}
    collecting_params = False
    for bit in bits:
        # Detect swap to params
        if bit == "?":
            if collecting_params:
                raise template.TemplateSyntaxError(
                    f"{tag_name} tag can only have one param section"
                )
            collecting_params = True
            continue

        # First we try to extract a potential kwarg from the bit
        kwarg = token_kwargs([bit], parser)
        if kwarg:
            # The kwarg was successfully extracted
            param, value = kwarg.popitem()

            if collecting_params:
                if param in params:
                    raise TemplateSyntaxError(
                        f"{tag_name} received multiple values for parameter argument {param}"
                    )
                params[param] = value
            else:
                if param in kwargs:
                    raise TemplateSyntaxError(
                        f"{tag_name} received multiple values for kwarg argument {param}"
                    )
                kwargs[param] = value
        else:
            if kwargs:
                raise TemplateSyntaxError(
                    f"{tag_name} received positional arguments after keyword arguments"
                )

            if collecting_params:
                raise TemplateSyntaxError(
                    f"{tag_name} received positional arguments instead of parameters"
                )

            args.append(parser.compile_filter(bit))

    return FragmentNode(view_name, args, kwargs, params)


class FragmentNode(template.Node):
    def __init__(self, view_name, args, kwargs, params):
        self.view_name = view_name
        self.args = args
        self.kwargs = kwargs
        self.params = params

    def render(self, context):
        view_name = self.view_name.resolve(context)
        args = [arg.resolve(context) for arg in self.args]
        kwargs = {k: v.resolve(context) for k, v in self.kwargs.items()}
        params = {k: v.resolve(context) for k, v in self.params.items()}

        url = reverse(view_name, args=args, kwargs=kwargs)
        resolver_match = resolve(url)
        view, view_args, view_kwargs = resolver_match

        # Build new request object
        orig_request = context["request"]
        factory = RequestFactory()
        action = getattr(factory, orig_request.method.lower())

        request = action(url, data=params)
        request.user = orig_request.user
        request.resolver_match = resolver_match

        response = view(*view_args, as_fragment=True, request=request, **view_kwargs)

        if isinstance(response, SimpleTemplateResponse):
            response = response.render()

        return mark_safe(response.content.decode())

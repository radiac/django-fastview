from copy import copy

from django import template
from django.http import QueryDict
from django.template import TemplateSyntaxError
from django.template.base import token_kwargs
from django.template.response import SimpleTemplateResponse
from django.urls import resolve, reverse
from django.utils.safestring import mark_safe


register = template.Library()


@register.simple_tag(name="breakpoint", takes_context=True)
def dev_breakpoint(context):
    """
    Internal developer tag to help debug templates
    """
    breakpoint()
    return ""


@register.filter
def formset_pk_name(formset):
    """
    Get the name of the primary key field for the given formset

    Can't access _meta within a template
    """
    return formset.model._meta.pk.name


@register.simple_tag(takes_context=True)
def urlparams(context, **kwargs):
    """
    Update the current GET params with the specified values, and return an URL-encoded
    string, preserving other params.

    Pass a ``None`` value to remove an existing param if it exists

    Usage::

        <a href="{% url .. %}?{% urlparams foo=bar remove=None %}">
    """
    params = context["request"].GET.copy()
    # Can't call params.update() - a QueryDict appends to existing, doesn't overwrite
    for key, value in kwargs.items():
        if value is None:
            if value in params:
                del params[key]
        else:
            params[key] = value
    querystring = params.urlencode()
    return querystring


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
        params = {k: str(v.resolve(context)) for k, v in self.params.items()}

        url = reverse(view_name, args=args, kwargs=kwargs)
        resolver_match = resolve(url)
        view, view_args, view_kwargs = resolver_match

        # Update request object with new path
        request = copy(context["request"])
        path_info_root = request.path[: len(request.path) - len(request.path_info)]
        request.path = url
        request.path_info = url[len(path_info_root) :]
        request.resolver_match = resolver_match

        if request.method == "GET":
            GET = QueryDict(mutable=True)
            GET.update(params)
            request.GET = GET
        else:
            # TODO: Add support for POST
            raise NotImplementedError("Fragments only support GET")

        # Perform the new request
        response = view(*view_args, as_fragment=True, request=request, **view_kwargs)

        if isinstance(response, SimpleTemplateResponse):
            response = response.render()
        else:
            # TODO: Add support for redirects eg from POST
            raise ValueError("Did not receive expected response from fragment view")

        response_content = mark_safe(response.content.decode())

        return response_content

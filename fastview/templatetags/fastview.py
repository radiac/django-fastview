from copy import copy

from django import template
from django.conf import settings
from django.http import QueryDict
from django.template import TemplateSyntaxError
from django.template.base import token_kwargs, Token, TokenType, FilterExpression
from django.template.response import SimpleTemplateResponse
from django.urls import resolve, reverse
from django.utils.safestring import mark_safe
from django.template.loader_tags import do_include, IncludeNode
from ..urls import urlparams
from ..views.mixins import FastViewMixin


register = template.Library()


@register.simple_tag(name="breakpoint", takes_context=True)
def dev_breakpoint(context):
    """
    Internal developer tag to help debug templates
    """
    if settings.DEBUG:
        breakpoint()
    return ""


@register.filter
def formset_pk_name(formset):
    """
    Get the name of the primary key field for the given formset

    Can't access _meta within a template
    """
    return formset.model._meta.pk.name


@register.simple_tag(name="urlparams", takes_context=True)
def template_urlparams(context, **kwargs):
    """
    Update the current GET params with the specified values, and return an URL-encoded
    string, preserving other params.

    Pass a ``None`` value to remove an existing param if it exists

    Usage::

        <a href="{% url .. %}?{% urlparams foo=bar remove=None %}">
    """
    return urlparams(context["request"].GET, **kwargs)


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


class FragmentComponentNode(IncludeNode):
    def render(self, context):
        # We're subclassing IncludeNode, which stores our component name as template
        component_name = self.template.resolve(context)
        if not isinstance(component_name, str):
            raise ValueError("Fragment component must be called with a name string")

        # Find the current view
        view = context.get("view")
        if not view or not isinstance(view, FastViewMixin):
            raise ValueError(
                "fragment_component can only be used in a fragment template"
            )

        # Get all potential fragment template names and turn them into component names
        names = view.get_fragment_template_names()
        components = [f"{name.rsplit('.',1)[0]}/{component_name}" for name in names]

        # Trick IncludeNode into using our list of components instead of the original
        # template name
        CONTEXT_VAR = "fastview_component_includes"
        old_template = self.template  # this should not be necessary, but just in case
        self.template = FilterExpression(CONTEXT_VAR, self.parser)
        with context.push(**{CONTEXT_VAR: components}):
            response = super().render(context)
        self.template = old_template
        return response


@register.tag("fragment_component")
def fragment_component(parser, token):
    """
    Generate a list of paths to look for the specified fragment component

    Example::

        {% fragment_component "data.html" %}
        {% fragment_component "data.html" with bar="1" %}
    """
    # We don't want to have to re-implement do_include, so just call it and swap the
    # class of the returned node, to get our FragmentComponentNode.render top of the MRO
    node = do_include(parser, token)
    node.__class__ = FragmentComponentNode
    node.parser = parser  # will need this for creating a FilterExpression
    return node

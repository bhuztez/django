from django.template import loader
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.regression import RegressionView
from django.contrib.auth import decorators

import warnings
warnings.warn(
    'Function-based generic views have been deprecated; use class-based views instead.',
    DeprecationWarning
)

class create_object(RegressionView):
    """
    Generic object-creation function.

    Templates: ``<app_label>/<model_name>_form.html``
    Context:
        form
            the form for the object
    """

    def __call__(self, request, model=None, template_name=None,
        template_loader=loader, extra_context=None, post_save_redirect=None,
        login_required=False, context_processors=None, form_class=None):

        view = CreateView.as_view(
            model=model,
            template_name=template_name,
            success_url=post_save_redirect,
            form_class=form_class)

        if login_required:
            view = decorators.login_required(view)

        return view(request)


class update_object(RegressionView):
    """
    Generic object-update function.

    Templates: ``<app_label>/<model_name>_form.html``
    Context:
        form
            the form for the object
        object
            the original object being edited
    """

    def __call__(self, request, model=None, object_id=None, slug=None,
        slug_field='slug', template_name=None, template_loader=loader,
        extra_context=None, post_save_redirect=None, login_required=False,
        context_processors=None, template_object_name='object',
        form_class=None):

        view = UpdateView.as_view(
            model=model,
            template_name=template_name,
            success_url=post_save_redirect,
            form_class=form_class,
            slug_field=slug_field)

        if login_required:
            view = decorators.login_required(view)

        return view(request, pk=object_id, slug=slug)


class delete_object(RegressionView):

    def __call__(self, request, model, post_delete_redirect, object_id=None,
        slug=None, slug_field='slug', template_name=None,
        template_loader=loader, extra_context=None, login_required=False,
        context_processors=None, template_object_name='object'):

        view = DeleteView.as_view(
            model=model,
            template_name=template_name,
            success_url=post_delete_redirect,
            slug_field=slug_field)

        if login_required:
            view = decorators.login_required(view)

        return view(request, pk=object_id, slug=slug)



from django.template import loader
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.regression import RegressionView


import warnings
warnings.warn(
    'Function-based generic views have been deprecated; use class-based views instead.',
    DeprecationWarning
)


class object_list(RegressionView):
    """
    Generic list of objects.

    Templates: ``<app_label>/<model_name>_list.html``
    Context:
        object_list
            list of objects
        is_paginated
            are the results paginated?
        results_per_page
            number of objects per page (if paginated)
        has_next
            is there a next page?
        has_previous
            is there a prev page?
        page
            the current page
        next
            the next page
        previous
            the previous page
        pages
            number of pages, total
        hits
            number of objects, total
        last_on_page
            the result number of the last of object in the
            object_list (1-indexed)
        first_on_page
            the result number of the first object in the
            object_list (1-indexed)
        page_range:
            A list of the page numbers (1-indexed).
    """

    def __call__(self, request, queryset, paginate_by=None, page=None,
        allow_empty=True, template_name=None, template_loader=loader,
        extra_context=None, context_processors=None, template_object_name='object',
        mimetype=None):
        
        view = ListView.as_view(
            queryset = queryset,
            paginate_by = paginate_by,
            template_name = template_name,
            context_object_name = template_object_name)
        return view(request, page=page)


class object_detail(RegressionView):

    def __call__(self, request, queryset, object_id=None, slug=None,
        slug_field='slug', template_name=None, template_name_field=None,
        template_loader=loader, extra_context=None,
        context_processors=None, template_object_name='object',
        mimetype=None):


        view = DetailView.as_view(
            queryset = queryset,
            slug_field = slug_field,
            template_name = template_name,
            context_object_name = template_object_name)
        return view(request, pk=object_id, slug=slug)




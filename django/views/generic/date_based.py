from django.template import loader

from django.views.generic.dates import (
    ArchiveIndexView, YearArchiveView, MonthArchiveView, 
    WeekArchiveView, DayArchiveView, TodayArchiveView, DateDetailView)
from django.views.generic.regression import RegressionView

import warnings
warnings.warn(
    'Function-based generic views have been deprecated; use class-based views instead.',
    DeprecationWarning
)


class archive_index(RegressionView):
    """
    Generic top-level archive of date-based objects.

    Templates: ``<app_label>/<model_name>_archive.html``
    Context:
        date_list
            List of years
        latest
            Latest N (defaults to 15) objects by date
    """

    def __call__(self, request, queryset, date_field, num_latest=15,
        template_name=None, template_loader=loader,
        extra_context=None, allow_empty=True, context_processors=None,
        mimetype=None, allow_future=False, template_object_name='latest'):

        view = ArchiveIndexView.as_view(
            queryset = queryset,
            date_field = date_field,
            template_name = template_name,
            allow_empty = allow_empty,
            allow_future = allow_future,
            context_object_name = template_object_name)

        return view(request)


class archive_year(RegressionView):
    """
    Generic yearly archive view.

    Templates: ``<app_label>/<model_name>_archive_year.html``
    Context:
        date_list
            List of months in this year with objects
        year
            This year
        object_list
            List of objects published in the given month
            (Only available if make_object_list argument is True)
    """
    def __call__(self, request, year, queryset, date_field, template_name=None,
        template_loader=loader, extra_context=None, allow_empty=False,
        context_processors=None, template_object_name='object', mimetype=None,
        make_object_list=False, allow_future=False):

        view = YearArchiveView.as_view(
            queryset = queryset,
            date_field = date_field,
            template_name = template_name,
            allow_empty = allow_empty,
            context_object_name = template_object_name,
            make_object_list = make_object_list,
            allow_future = allow_future)
        
        return view(request, year=year)


class archive_month(RegressionView):
    """
    Generic monthly archive view.

    Templates: ``<app_label>/<model_name>_archive_month.html``
    Context:
        date_list:
            List of days in this month with objects
        month:
            (date) this month
        next_month:
            (date) the first day of the next month, or None if the next month is in the future
        previous_month:
            (date) the first day of the previous month
        object_list:
            list of objects published in the given month
    """
    def __call__(self, request, year, month, queryset, date_field,
        month_format='%b', template_name=None, template_loader=loader,
        extra_context=None, allow_empty=False, context_processors=None,
        template_object_name='object', mimetype=None, allow_future=False):

        view = MonthArchiveView.as_view(
            queryset = queryset,
            date_field = date_field,
            month_format=month_format,
            template_name = template_name,
            allow_empty = allow_empty,
            context_object_name = template_object_name,
            allow_future = allow_future)
        
        return view(request, year=year, month=month)


class archive_week(RegressionView):
    """
    Generic weekly archive view.

    Templates: ``<app_label>/<model_name>_archive_week.html``
    Context:
        week:
            (date) this week
        object_list:
            list of objects published in the given week
    """
    def __call__(self, request, year, week, queryset, date_field,
        template_name=None, template_loader=loader,
        extra_context=None, allow_empty=True, context_processors=None,
        template_object_name='object', mimetype=None, allow_future=False):

        view = WeekArchiveView.as_view(
            queryset = queryset,
            date_field = date_field,
            template_name = template_name,
            allow_empty = allow_empty,
            context_object_name = template_object_name,
            allow_future = allow_future)
        
        return view(request, year=year, week=week)


class archive_day(RegressionView):
    """
    Generic daily archive view.

    Templates: ``<app_label>/<model_name>_archive_day.html``
    Context:
        object_list:
            list of objects published that day
        day:
            (datetime) the day
        previous_day
            (datetime) the previous day
        next_day
            (datetime) the next day, or None if the current day is today
    """

    def __call__(self, request, year, month, day, queryset, date_field,
        month_format='%b', day_format='%d', template_name=None,
        template_loader=loader, extra_context=None, allow_empty=False,
        context_processors=None, template_object_name='object',
        mimetype=None, allow_future=False):

        view = DayArchiveView.as_view(
            queryset = queryset,
            date_field = date_field,
            month_format = month_format,
            day_format = day_format,
            template_name = template_name,
            allow_empty = allow_empty,
            context_object_name = template_object_name,
            allow_future = allow_future)
        
        return view(request, year=year, month=month, day=day)


class archive_today(RegressionView):
    """
    Generic daily archive view for today. Same as archive_day view.
    """

    def __call__(self, request, **kwargs):
        view = TodayArchiveView.as_view()
        return view(request, **kwargs)


class object_detail(RegressionView):
    """
    Generic detail view from year/month/day/slug or year/month/day/id structure.

    Templates: ``<app_label>/<model_name>_detail.html``
    Context:
        object:
            the object to be detailed
    """
    def __call__(self, request, year, month, day, queryset, date_field,
        month_format='%b', day_format='%d', object_id=None, slug=None,
        slug_field='slug', template_name=None, template_name_field=None,
        template_loader=loader, extra_context=None, context_processors=None,
        template_object_name='object', mimetype=None, allow_future=False):


        view = DateDetailView.as_view(
            queryset = queryset,
            date_field = date_field,
            month_format = month_format,
            day_format = day_format,
            slug_field = slug_field,
            template_name = template_name,
            context_object_name = template_object_name,
            allow_future = allow_future)
        
        return view(request, year=year, month=month, day=day, pk=object_id, slug=slug)



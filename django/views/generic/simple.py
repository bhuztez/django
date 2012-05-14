from django.template import loader, RequestContext
from django.http import HttpResponse
from django.utils.log import getLogger
from django.views.generic.base import RedirectView
from django.views.generic.regression import RegressionView


import warnings
warnings.warn(
    'Function-based generic views have been deprecated; use class-based views instead.',
    DeprecationWarning
)

logger = getLogger('django.request')


def direct_to_template(request, template, extra_context=None, mimetype=None, **kwargs):
    """
    Render a given template with any extra URL parameters in the context as
    ``{{ params }}``.
    """
    if extra_context is None: extra_context = {}
    dictionary = {'params': kwargs}
    for key, value in extra_context.items():
        if callable(value):
            dictionary[key] = value()
        else:
            dictionary[key] = value
    c = RequestContext(request, dictionary)
    t = loader.get_template(template)
    return HttpResponse(t.render(c), content_type=mimetype)


class redirect_to(RegressionView):
    """
    Redirect to a given URL.

    The given url may contain dict-style string formatting, which will be
    interpolated against the params in the URL.  For example, to redirect from
    ``/foo/<id>/`` to ``/bar/<id>/``, you could use the following URLconf::

        urlpatterns = patterns('',
            ('^foo/(?P<id>\d+)/$', 'django.views.generic.simple.redirect_to', {'url' : '/bar/%(id)s/'}),
        )

    If the given url is ``None``, a HttpResponseGone (410) will be issued.

    If the ``permanent`` argument is False, then the response will have a 302
    HTTP status code. Otherwise, the status code will be 301.

    If the ``query_string`` argument is True, then the GET query string
    from the request is appended to the URL.

    """

    def __call__(self, request, url, permanent=True, query_string=False, **kwargs):
        view = RedirectView.as_view(url=url, permanent=permanent, query_string=query_string)
        return view(request, **kwargs)



"""
Views and functions for serving static files. These are only to be used during
development, and SHOULD NOT be used in a production setting.

"""
import os
import posixpath
try:
    from urllib.parse import unquote
except ImportError:     # Python 2
    from urllib import unquote

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse, Http404
from django.views import static

from django.contrib.staticfiles import finders

def serve(request, path, document_root=None, insecure=False, **kwargs):
    """
    Serve static files below a given point in the directory structure or
    from locations inferred from the staticfiles finders.

    To use, put a URL pattern such as::

        (r'^(?P<path>.*)$', 'django.contrib.staticfiles.views.serve')

    in your URLconf.

    It uses the django.views.static view to serve the found files.
    """
    if not settings.DEBUG and not insecure:
        raise ImproperlyConfigured("The staticfiles view can only be used in "
                                   "debug mode or if the the --insecure "
                                   "option of 'runserver' is used")
    normalized_path = posixpath.normpath(unquote(path)).lstrip('/')
    storage_path = finders.find(normalized_path)
    if storage_path is None:
        raise Http404("'%s' could not be found" % path)
    storage, relative_path = storage_path
    if storage.isdir(relative_path):
        raise Http404("Directory indexes are not allowed here.")
    return HttpResponse(storage.open(relative_path))


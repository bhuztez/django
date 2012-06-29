"""
Wrapper for loading templates from "templates" directories in INSTALLED_APPS
packages.
"""

import os
import sys

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import AppDirectoryStorage
from django.template.base import TemplateDoesNotExist
from django.template.loader import BaseLoader



class Loader(BaseLoader):
    is_usable = True

    def __init__(self, apps=None):
        self.apps = apps
        if apps is None:
            self.apps = settings.INSTALLED_APPS
        self.reset()

    def reset(self):
        app_template_storages = []
        for app in self.apps:
            storage = AppDirectoryStorage(app, 'templates')
            if storage.isdir(''):
                app_template_storages.append(storage)

        self.app_template_storages = tuple(app_template_storages)

    def load_template_source(self, template_name):
        for storage in self.app_template_storages:
            if storage.exists(template_name):
                with storage.open(template_name, 'rb') as fp:
                    return (fp.read().decode(settings.FILE_CHARSET), template_name)

        raise TemplateDoesNotExist(template_name)

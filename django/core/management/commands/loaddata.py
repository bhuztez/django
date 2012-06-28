from __future__ import unicode_literals

import os
import gzip
import zipfile
from optparse import make_option

from django.conf import settings
from django.core import serializers
from django.core.files.storage import FileSystemStorage, AppDirectoryStorage
from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import no_style
from django.db import (connections, router, transaction, DEFAULT_DB_ALIAS,
      IntegrityError, DatabaseError)
from django.db.models import get_apps
from django.utils.encoding import force_text
from itertools import product

try:
    import bz2
    has_bz2 = True
except ImportError:
    has_bz2 = False


class Command(BaseCommand):
    help = 'Installs the named fixture(s) in the database.'
    args = "fixture [fixture ...]"

    option_list = BaseCommand.option_list + (
        make_option('--database', action='store', dest='database',
            default=DEFAULT_DB_ALIAS, help='Nominates a specific database to load '
                'fixtures into. Defaults to the "default" database.'),
        make_option('--ignorenonexistent', '-i', action='store_true', dest='ignore',
            default=False, help='Ignores entries in the serialized data for fields'
                                ' that do not currently exist on the model.'),
    )

    def handle(self, *fixture_labels, **options):

        self.ignore = options.get('ignore')
        self.using = options.get('database')

        connection = connections[self.using]

        if not len(fixture_labels):
            raise CommandError(
                "No database fixture specified. Please provide the path of at "
                "least one fixture in the command line."
            )

        self.verbosity = int(options.get('verbosity'))

        # commit is a stealth option - it isn't really useful as
        # a command line option, but it can be useful when invoking
        # loaddata from within another script.
        # If commit=True, loaddata will use its own transaction;
        # if commit=False, the data load SQL will become part of
        # the transaction in place when loaddata was invoked.
        commit = options.get('commit', True)

        # Keep a count of the installed objects and fixtures
        self.fixture_count = 0
        self.loaded_object_count = 0
        self.fixture_object_count = 0
        self.models = set()

        # Get a cursor (even though we don't need one yet). This has
        # the side effect of initializing the test database (if
        # it isn't already initialized).
        cursor = connection.cursor()

        # Start transaction management. All fixtures are installed in a
        # single transaction to ensure that all references are resolved.
        if commit:
            transaction.commit_unless_managed(using=self.using)
            transaction.enter_transaction_management(using=self.using)
            transaction.managed(True, using=self.using)

        class SingleZipReader(zipfile.ZipFile):
            def __init__(self, storage, path, mode, *args, **kwargs):
                fileobj = storage.open(path, mode)
                zipfile.ZipFile.__init__(self, fileobj, *args, **kwargs)
                if settings.DEBUG:
                    assert len(self.namelist()) == 1, "Zip-compressed fixtures must contain only one file."
            def read(self):
                return zipfile.ZipFile.read(self, self.namelist()[0])

        class GzipFileReader(gzip.GzipFile):
            def __init__(self, storage, path, mode, *args, **kwargs):
                fileobj = storage.open(path, mode)
                gzip.GzipFile.__init__(self, fileobj, *args, **kwargs)

        class _BZ2FileReader(object):
            def __init__(self, storage, path, mode):
                self.fileobj = storage.open(path, mode)

            def read(self):
                return bz2.BZ2Decompressor(self.fileobj.read())

            def close(self):
                self.fileobj.close()

        def BZ2FileReader(storage, path, mode):
            try:
                absolute_path = storage.path(path)
                return bz2.BZ2File(absolute_path, mode=mode)
            except NotImplementedError:
                return _BZ2FileReader(storage, path, mode)
            

        self.compression_types = {
            None:   lambda storage, path, mode: storage.open(path, mode),
            'gz':   GzipFileReader,
            'zip':  SingleZipReader
        }
        if has_bz2:
            self.compression_types['bz2'] = BZ2FileReader

        app_fixture_storages = []
        for app in get_apps():
            storage = AppDirectoryStorage(app.__name__[:-7], 'fixtures')
            if storage.isdir(''):
                app_fixture_storages.append(storage)

        try:
            with connection.constraint_checks_disabled():
                for fixture_label in fixture_labels:
                    self.load_label(fixture_label, app_fixture_storages)

            # Since we disabled constraint checks, we must manually check for
            # any invalid keys that might have been added
            table_names = [model._meta.db_table for model in self.models]
            try:
                connection.check_constraints(table_names=table_names)
            except Exception as e:
                e.args = ("Problem installing fixtures: %s" % e,)
                raise

        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            if commit:
                transaction.rollback(using=self.using)
                transaction.leave_transaction_management(using=self.using)
            raise

        # If we found even one object in a fixture, we need to reset the
        # database sequences.
        if self.loaded_object_count > 0:
            sequence_sql = connection.ops.sequence_reset_sql(no_style(), self.models)
            if sequence_sql:
                if self.verbosity >= 2:
                    self.stdout.write("Resetting sequences\n")
                for line in sequence_sql:
                    cursor.execute(line)

        if commit:
            transaction.commit(using=self.using)
            transaction.leave_transaction_management(using=self.using)

        if self.verbosity >= 1:
            if self.fixture_object_count == self.loaded_object_count:
                self.stdout.write("Installed %d object(s) from %d fixture(s)" % (
                    self.loaded_object_count, self.fixture_count))
            else:
                self.stdout.write("Installed %d object(s) (of %d) from %d fixture(s)" % (
                    self.loaded_object_count, self.fixture_object_count, self.fixture_count))

        # Close the DB connection. This is required as a workaround for an
        # edge case in MySQL: if the same connection is used to
        # create tables, load data, and query, the query can return
        # incorrect results. See Django #7572, MySQL #37735.
        if commit:
            connection.close()

    def load_label(self, fixture_label, app_fixture_storages):

        parts = fixture_label.split('.')

        if len(parts) > 1 and parts[-1] in self.compression_types:
            compression_formats = [parts[-1]]
            parts = parts[:-1]
        else:
            compression_formats = self.compression_types.keys()

        if len(parts) == 1:
            fixture_name = parts[0]
            formats = serializers.get_public_serializer_formats()
        else:
            fixture_name, format = '.'.join(parts[:-1]), parts[-1]
            if format in serializers.get_public_serializer_formats():
                formats = [format]
            else:
                formats = []

        if formats:
            if self.verbosity >= 2:
                self.stdout.write("Loading '%s' fixtures..." % fixture_name)
        else:
            raise CommandError(
                "Problem installing fixture '%s': %s is not a known serialization format." %
                    (fixture_name, format))

        if os.path.isabs(fixture_name):
            fixture_storages = [FileSystemStorage(fixture_name)]
        else:
            fixture_storages = app_fixture_storages + list(map(FileSystemStorage, settings.FIXTURE_DIRS)) + [FileSystemStorage('')]

        for fixture_storage in fixture_storages:
            self.process_storage(fixture_storage, fixture_name, compression_formats,
                             formats)

    def process_storage(self, fixture_storage, fixture_name, compression_formats,
                    serialization_formats):

        # humanize = lambda dirname: "'%s'" % dirname if dirname else 'absolute path'

        if self.verbosity >= 2:
            # self.stdout.write("Checking %s for fixtures..." % humanize(fixture_dir))
            self.stdout.write("Checking %s for fixtures..." % str(fixture_storage))

        label_found = False
        for combo in product([self.using, None], serialization_formats, compression_formats):
            database, format, compression_format = combo
            file_name = '.'.join(
                p for p in [
                    fixture_name, database, format, compression_format
                ]
                if p
            )

            if self.verbosity >= 3:
                # self.stdout.write("Trying %s for %s fixture '%s'..." % \
                #     (humanize(fixture_dir), file_name, fixture_name))
                self.stdout.write("Trying %s for %s fixture '%s'..." % \
                    (str(fixture_storage), file_name, fixture_name))

            open_method = self.compression_types[compression_format]
            try:
                fixture = open_method(fixture_storage, file_name, 'r')
            except IOError:
                if self.verbosity >= 2:
                    # self.stdout.write("No %s fixture '%s' in %s." % \
                    #    (format, fixture_name, humanize(fixture_dir)))
                    self.stdout.write("No %s fixture '%s' in %s." % \
                        (format, fixture_name, str(fixture_storage)))
            else:
                try:
                    if label_found:
                        # raise CommandError("Multiple fixtures named '%s' in %s. Aborting." %
                        #    (fixture_name, humanize(fixture_dir)))
                        raise CommandError("Multiple fixtures named '%s' in %s. Aborting." %
                            (fixture_name, str(fixture_storage)))

                    self.fixture_count += 1
                    objects_in_fixture = 0
                    loaded_objects_in_fixture = 0
                    if self.verbosity >= 2:
                        # self.stdout.write("Installing %s fixture '%s' from %s." % \
                        #    (format, fixture_name, humanize(fixture_dir)))
                        self.stdout.write("Installing %s fixture '%s' from %s." % \
                            (format, fixture_name, str(fixture_storage)))

                    objects = serializers.deserialize(format, fixture, using=self.using, ignorenonexistent=self.ignore)

                    for obj in objects:
                        objects_in_fixture += 1
                        if router.allow_syncdb(self.using, obj.object.__class__):
                            loaded_objects_in_fixture += 1
                            self.models.add(obj.object.__class__)
                            try:
                                obj.save(using=self.using)
                            except (DatabaseError, IntegrityError) as e:
                                e.args = ("Could not load %(app_label)s.%(object_name)s(pk=%(pk)s): %(error_msg)s" % {
                                        'app_label': obj.object._meta.app_label,
                                        'object_name': obj.object._meta.object_name,
                                        'pk': obj.object.pk,
                                        'error_msg': force_text(e)
                                    },)
                                raise

                    self.loaded_object_count += loaded_objects_in_fixture
                    self.fixture_object_count += objects_in_fixture
                    label_found = True
                except Exception as e:
                    if not isinstance(e, CommandError):
                        # e.args = ("Problem installing fixture '%s': %s" % (full_path, e),)
                        e.args = ("Problem installing fixture '%s': %s" % (str(fixture_storage)+file_name, e),)
                    raise
                finally:
                    fixture.close()

                # If the fixture we loaded contains 0 objects, assume that an
                # error was encountered during fixture loading.
                if objects_in_fixture == 0:
                    raise CommandError(
                        "No fixture data found for '%s'. (File format may be invalid.)" %
                            (fixture_name))

# Part of Odoo. See LICENSE file for full copyright and licensing details.

"""
OpenERP - Server
OpenERP is an ERP+CRM program for small and medium businesses.

The whole source code is distributed under the terms of the
GNU Public Licence.

(c) 2003-TODAY, Fabien Pinckaers - OpenERP SA
"""

import atexit
import csv # pylint: disable=deprecated-module
import logging
import os
import re
import sys

from psycopg2.errors import InsufficientPrivilege

import odoo
import odoo.release

from . import Command

__author__ = odoo.release.author
__version__ = odoo.release.version

# Also use the `odoo` logger for the main script.
_logger = logging.getLogger('odoo')

re._MAXCACHE = 4096  # default is 512, a little too small for odoo

def check_root_user():
    """Warn if the process's user is 'root' (on POSIX system)."""
    if os.name == 'posix':
        import getpass
        if getpass.getuser() == 'root':
            sys.stderr.write("Running as user 'root' is a security risk.\n")

def check_postgres_user():
    """ Exit if the configured database user is 'postgres'.

    This function assumes the configuration has been initialized.
    """
    config = odoo.tools.config
    if (config['db_user'] or os.environ.get('PGUSER')) == 'postgres':
        sys.stderr.write("Using the database user 'postgres' is a security risk, aborting.")
        sys.exit(1)

def report_configuration():
    """ Log the server version and some configuration values.

    This function assumes the configuration has been initialized.
    """
    config = odoo.tools.config
    _logger.info("Odoo version %s", __version__)
    if os.path.isfile(config['config']):
        _logger.info("Using configuration file at %s", config['config'])
    _logger.info('addons paths: %s', odoo.addons.__path__)
    if config.get('upgrade_path'):
        _logger.info('upgrade path: %s', config['upgrade_path'])
    host = config['db_host'] or os.environ.get('PGHOST', 'default')
    port = config['db_port'] or os.environ.get('PGPORT', 'default')
    user = config['db_user'] or os.environ.get('PGUSER', 'default')
    _logger.info('database: %s@%s:%s', user, host, port)
    replica_host = config['db_replica_host']
    replica_port = config['db_replica_port']
    if replica_host or replica_port:
        _logger.info('replica database: %s@%s:%s', user, replica_host or 'default', replica_port or 'default')
    if sys.version_info[:2] > odoo.release.MAX_PY_VERSION:
        _logger.warning("Python %s is not officially supported, please use Python %s instead",
            '.'.join(map(str, sys.version_info[:2])),
            '.'.join(map(str, odoo.release.MAX_PY_VERSION))
        )

def rm_pid_file(main_pid):
    config = odoo.tools.config
    if config['pidfile'] and main_pid == os.getpid():
        try:
            os.unlink(config['pidfile'])
        except OSError:
            pass

def setup_pid_file():
    """ Create a file with the process id written in it.

    This function assumes the configuration has been initialized.
    """
    config = odoo.tools.config
    if not odoo.evented and config['pidfile']:
        pid = os.getpid()
        with open(config['pidfile'], 'w') as fd:
            fd.write(str(pid))
        atexit.register(rm_pid_file, pid)

def export_translation():
    config = odoo.tools.config
    dbnames = config['db_name']
    if len(dbnames) > 1:
        sys.exit("-d/--database/db_name has multiple database, please provide a single one")
    if config["language"]:
        msg = "language %s" % (config["language"],)
    else:
        msg = "new language"
    _logger.info('writing translation file for %s to %s', msg,
        config["translate_out"])

    fileformat = os.path.splitext(config["translate_out"])[-1][1:].lower()
    # .pot is the same fileformat as .po
    if fileformat == "pot":
        fileformat = "po"

    with open(config["translate_out"], "wb") as buf:
        registry = odoo.modules.registry.Registry.new(dbnames[0])
        with registry.cursor() as cr:
            odoo.tools.translate.trans_export(config["language"],
                config["translate_modules"] or ["all"], buf, fileformat, cr)

    _logger.info('translation file written successfully')

def import_translation():
    config = odoo.tools.config
    overwrite = config["overwrite_existing_translations"]
    dbnames = config['db_name']
    if len(dbnames) > 1:
        sys.exit("-d/--database/db_name has multiple database, please provide a single one")
    registry = odoo.modules.registry.Registry.new(dbnames[0])
    with registry.cursor() as cr:
        translation_importer = odoo.tools.translate.TranslationImporter(cr)
        translation_importer.load_file(config["translate_in"], config["language"])
        translation_importer.save(overwrite=overwrite)

def main(args):
    check_root_user()
    odoo.tools.config.parse_config(args, setup_logging=True)
    check_postgres_user()
    report_configuration()

    config = odoo.tools.config

    # the default limit for CSV fields in the module is 128KiB, which is not
    # quite sufficient to import images to store in attachment. 500MiB is a
    # bit overkill, but better safe than sorry I guess
    csv.field_size_limit(500 * 1024 * 1024)

    for db_name in config['db_name']:
        try:
            odoo.service.db._create_empty_database(db_name)
            config['init']['base'] = True
        except InsufficientPrivilege as err:
            # We use an INFO loglevel on purpose in order to avoid
            # reporting unnecessary warnings on build environment
            # using restricted database access.
            _logger.info("Could not determine if database %s exists, "
                         "skipping auto-creation: %s", db_name, err)
        except odoo.service.db.DatabaseExists:
            pass

    if config["translate_out"]:
        export_translation()
        sys.exit(0)

    if config["translate_in"]:
        import_translation()
        sys.exit(0)

    stop = config["stop_after_init"]

    setup_pid_file()
    rc = odoo.service.server.start(preload=config['db_name'], stop=stop)
    sys.exit(rc)


class Server(Command):
    """Start the odoo server (default command)"""

    def run(self, args):
        odoo.tools.config.parser.prog = self.prog
        main(args)

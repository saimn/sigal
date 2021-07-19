from pickle import loads, dumps
import logging
import os
from os.path import isfile
import sqlite3

from .utils import get_mod_date


class Cache:
    """
    Uses sqlite3 to cache file data for faster lookup.

    A cache is considered good if the file modification date is accurate
    to the second.

    Cache contents can either be a string or a dict (such as metadata).
    """
    def __init__(self, settings):
        self.settings = settings
        self.con = None
        self.logger = logging.getLogger(__name__)

    def __enter__(self):
        if (not self.con) and self.settings.get('cache', None):
            self.con = sqlite3.connect(':memory:')
            if isfile(self.settings['cache']):
                self.logger.info('Loading cache from file %s',
                                 self.settings['cache'])
                try:
                    disk_con = sqlite3.connect(self.settings['cache'])
                    with self.con:
                        disk_con.backup(self.con)
                    disk_con.close()
                except sqlite3.OperationalError:
                    self.logger.warning('Cache db is corrupt, deleting')
                    os.remove(self.settings['cache'])

            sql = ('CREATE TABLE IF NOT EXISTS '
                   'cache(path NOT NULL PRIMARY KEY, mod, data)')
            self.con.execute(sql)

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.con:
            return

        if (not exc_type) and self.settings.get('cache', None):
            self.logger.info('Saving cache to file %s',
                             self.settings['cache'])
            disk_con = sqlite3.connect(self.settings['cache'])
            with disk_con:
                self.con.backup(disk_con)
            disk_con.close()
        self.con.close()
        self.con = None

    def read(self, path):
        if not self.con:
            return None

        self.logger.debug('Reading from cache: %s', path)

        mod_date = int(get_mod_date(path))

        cur = self.con.execute('SELECT mod,data FROM cache WHERE path = ?',
                               (path, ))
        row = cur.fetchone()

        if row and mod_date == row[0]:
            return row[1]
        else:
            return None

    def read_dict(self, path):
        if not self.con:
            return None

        data = self.read(path)
        if data:
            return loads(data)
        else:
            return None

    def write(self, path, data):
        if not self.con:
            return

        self.logger.debug('Writing to cache: %s', path)

        mod_date = int(get_mod_date(path))

        self.con.execute('REPLACE INTO cache (path, mod, data) VALUES (?, ?, ?)',
                         (path, mod_date, data))
        self.con.commit()

    def write_dict(self, path, data):
        if not self.con:
            return

        self.write(path, dumps(data))

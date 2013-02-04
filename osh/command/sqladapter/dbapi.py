# osh
# Copyright (C) Jack Orenstein <jao@geophile.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import osh.command.sql

CURSOR_ARRAYSIZE = 20

class DBAPI(osh.command.sql._DBType):

    def connect(self, connect_info):
        connect_args = []
        driver = None
        for key, value in connect_info.iteritems():
            if key == 'driver':
                driver = value
            else:
                connect_args.append("%s = '%s'" % (key, value))
        connect_statement = '%s.connect(%s)' % (driver, ', '.join(connect_args))
        exec('import %s' % driver)
        connection = _Connection(eval(connect_statement))
        return connection

    def run_query(self, connection, query, inputs):
        cursor = connection.cursor
        cursor.execute(query, inputs)
        if cursor.description is None:
            # No query result
            rowcount = cursor.rowcount
            connection.commit()
            yield rowcount
        else:
            rows = cursor.fetchmany()
            while len(rows) > 0:
                for row in rows:
                    yield row
                rows = cursor.fetchmany()

    def close_connection(self, connection):
        connection.close()

class _Connection(object):

    connection = None
    cursor = None

    def __init__(self, connection):
        self.connection = connection
        self.cursor = connection.cursor()
        self.cursor.arraysize = CURSOR_ARRAYSIZE

    def commit(self):
        self.connection.commit()

    def close(self):
        self.connection.close()

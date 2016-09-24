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

"""C{sql [DB] QUERY}

Executes a sql query on a specified database.  Occurrences of
formatting directives (e.g. C{%s}) will be replaced by input values.

The database is selected by C{DB}. If C{DB} matches an C{osh.sql}
profile in C{.oshrc}, then the database is specified by that
profile. If C{DB} is omitted, then the default profile is used.

If C{QUERY} is a SELECT statement, then the query is executed and
output rows, represented by tuples, are written to output.  If C{QUERY}
is any other type of SQL statement, then no output is written.
"""

import os

import osh.loader
import osh.core

# CLI
def _sql():
    return _Sql()

# API
def sql(query, db = None):
    """Executes a sql query on a specified database.  Occurrences of
    formatting directives (e.g. C{%s}) will be replaced by input values.
    The database is selected by C{db}. If C{db} matches an C{osh.sql}
    profile in C{.oshrc}, then the database is specified by that
    profile. If C{db} is C{None}, then the default profile is used.
    If C{QUERY} is a I{select} statement, then the query is executed and
    output rows, represented by tuples, are written to output. If C{QUERY}
    is any other type of SQL statement, then no output is written.
    """
    args = []
    if db:
        args.append(db)
    args.append(query)
    return _Sql().process_args(*args)

def _tuple_like(object):
    return isinstance(object, list) or isinstance(object, tuple)

class _Sql(osh.core.Generator):

    _db_type = None
    _host = None
    _db = None
    _header = None
    _user = None
    _password = None
    _connection = None
    _query = None


    # object interface

    def __init__(self):
        osh.core.Generator.__init__(self, '', (1, 2))


    # OshCommand interface
    
    def doc(self):
        return __doc__

    def setup(self):
        args = self.args()
        db_profile = None
        if args.has_next():
            query = args.next_string()
            if args.has_next():
                db_profile = query
                query = args.next_string()
                if args.has_next():
                    self.usage()
        else:
            self.usage()
        if not db_profile:
            db_profile_from_env = osh.core.default_db_profile
            if db_profile_from_env:
                db_profile = db_profile_from_env
            else:
                db_profile = osh.core.config_value('sql')
        if not db_profile:
            raise Exception('No db profile selected')
        # query
        self._query = query
        # schema
        if self.thread_state and type(self.thread_state) is osh.cluster.Host:
            schema = self.thread_state.schema
        else:
            schema = None
        # connection info
        driver = osh.core.config_value('sql', db_profile, 'driver')
        dbtype = osh.core.config_value('sql', db_profile, 'dbtype')
        if dbtype is None and driver is None:
            raise Exception('Database configuration osh.sql.%s must configure either dbtype or driver' %
                            db_profile)
        elif driver:
            connect_info = osh.core.config_subset('sql.%s' % db_profile)
            # Make sure set_schema specification is gone for establishing connection
            try:
                del connect_info['set_schema']
            except KeyError:
                pass
            import sqladapter.dbapi
            self._db_type = sqladapter.dbapi.DBAPI()
            self._connection = self._db_type.connect(connect_info)
        elif dbtype:
            host = osh.core.config_value('sql', db_profile, 'host')
            if host is None:
                host = 'localhost'
            db = osh.core.config_value('sql', db_profile, 'db')
            user = osh.core.config_value('sql', db_profile, 'user')
            password = osh.core.config_value('sql', db_profile, 'password')
            # Load dbtype module and connect
            self._db_type = osh.loader.load_and_create(dbtype)
            self._connection = self._db_type.connect(db, host, user, password)
        else:
            assert False
        set_schema_query = osh.core.config_value('sql', db_profile, 'set_schema')
        if set_schema_query and self.thread_state:
            schema = self.thread_state.schema
            self._db_type.run_update(self._connection, set_schema_query % schema, [])


    # Generator interface

    def execute(self):
        # If this command is the first in a pipeline, then execute will be
        # called.
        self._execute_query([])

    # Receiver interface

    def receive(self, object):
        self._execute_query(object)

    def receive_complete(self):
        self._connection.close()
        self.send_complete()

    # For use by this class

    def _execute_query(self, inputs):
        for row in self._db_type.run_query(self._connection,
                                           self._query,
                                           inputs):
            self.send(row)

class _DBType(object):
    
    def connect(self, db, host, user, password):
        assert False

    def run_query(self, connection, query, inputs):
        assert False

    def close_connection(self, connection):
        assert False

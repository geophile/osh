# osh
# Copyright (C) 2005 Jack Orenstein <jao@geophile.com>
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

import _pg

from osh.command.sql import _DBType

def _postgres():
    return _SqlPostgres()

class _SqlPostgres(_DBType):

    def __init__(self):
        # The problem is that run_update is discontinued. Need to determine in run_query
        # if we have a result set or an update count.
        raise Exception('postgres adapter is broken. Use dbapi')

    def connect(self, db, host, user, password):
        try:
            return _pg.connect(db, host, -1, None, None, user, password)
        except _pg.Error, e:
            raise Exception('Unable to connect to %s: %s' % (db, str(e)))

    def run_query(self, connection, query, inputs):
        query = _bind(query, inputs)
        try:
            query_execution = connection.query(query)
            if query_execution:
                query_result = query_execution.getresult()
                for query_row in query_result:
                    yield query_row
        except _pg.Error, e:
            raise Exception('Error during execution of query %s: %s' % (query, str(e)))

    def run_update(self, connection, query, inputs):
        query = _bind(query, inputs)
        try:
            return connection.query(query)
        except _pg.Error, e:
            raise Exception('Error during execution of update %s: %s' % (query, str(e)))

    def close_connection(self, connection):
        connection.close()
        
def _bind(query, inputs):
    if type(inputs) not in (list, tuple):
        inputs = (inputs,)
    for value in inputs:
        query = query.replace('%s', str(value), 1)
    return query

# # osh
# # Copyright (C) Jack Orenstein <jao@geophile.com>
# #
# # This program is free software; you can redistribute it and/or modify
# # it under the terms of the GNU General Public License as published by
# # the Free Software Foundation; either version 2 of the License, or
# # (at your option) any later version.
# #
# # This program is distributed in the hope that it will be useful,
# # but WITHOUT ANY WARRANTY; without even the implied warranty of
# # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# # GNU General Public License for more details.
# #
# # You should have received a copy of the GNU General Public License
# # along with this program; if not, write to the Free Software
# # Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
# 
# from osh.external.pg8000 import dbapi
# 
# import osh.command.sql
# 
# CURSOR_ARRAYSIZE = 20
# 
# def _postgres():
#     return _Postgres()
# 
# class _Postgres(osh.command.sql._DBType):
# 
#     def connect(self, db, host, user, password):
#         try:
#             return _Connection(dbapi.connect(host = host, database = db, user = user, password = password))
#         except dbapi.Error, e:
#             raise Exception('Unable to connect to %s: %s' % (db, str(e)))
# 
#     def run_query(self, connection, query, inputs):
#         cursor = connection.cursor
#         try:
#             cursor.execute(query, inputs)
#             rows = cursor.fetchmany()
#             while len(rows) > 0:
#                 for row in rows:
#                     yield row
#                 rows = cursor.fetchmany()
#         except dbapi.Error, e:
#             raise Exception('Error during execution of query %s: %s' % (query, str(e)))
# 
#     def run_update(self, connection, query, inputs):
#         try:
#             cursor = connection.cursor
#             cursor.execute(query, inputs)
#             rowcount = cursor.rowcount
#             connection.commit()
#             return rowcount
#         except dbapi.Error, e:
#             raise Exception('Error during execution of update %s: %s' % (query, str(e)))
#         
# 
# class _Connection(object):
# 
#     connection = None
#     cursor = None
# 
#     def __init__(self, connection):
#         self.connection = connection
#         self.cursor = connection.cursor()
#         self.cursor.arraysize = CURSOR_ARRAYSIZE
# 
#     def commit(self):
#         self.connection.commit()

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

"""C{unique [-c]}

Input objects are passed to output, removing duplicates. No output is
generated until the end of the input stream occurs. However, if the
duplicates are known to be consecutive, then specifying C{-c} allows
output to be generated sooner. Input order is preserved only if C{-c}
is specified.

"""

import types

import osh.args
import osh.core

Option = osh.args.Option

# CLI
def _unique():
    return _Unique()

# API
def unique(consecutive = False):
    """Input objects are passed to output, removing duplicates. No output
    is generated until the end of the input stream occurs. However, if the
    duplicates are known to be consecutive, then setting C{consecutive} to true
    allows output to be generated sooner. Input order is preserved only if
    C{consecutive} is true.
    """
    args = []
    if consecutive:
        args.append(Option('-c'))
    return _Unique().process_args(*args)

class _Unique(osh.core.Op):

    _uniquer = None


    # object interface

    def __init__(self):
        osh.core.Op.__init__(self, 'c', (0, 0))


    # BaseOp interface

    def doc(self):
        return __doc__

    def setup(self):
        args = self.args()
        if args.has_next():
            self.usage()
        if args.flag('-c'):
            self._uniquer = _ConsecutiveUniquer(self)
        else:
            self._uniquer = _GeneralUniquer(self)

    def receive(self, object):
        self._uniquer.receive(object)

    def receive_complete(self):
        self._uniquer.receive_complete()


class _GeneralUniquer(object):

    _command = None
    _unique = None

    def __init__(self, command):
        self._command = command
        self._unique = {}

    def receive(self, object):
        if type(object) == types.ListType:
            object = tuple(object)
        self._unique[object] = None

    def receive_complete(self):
        for key in self._unique.keys():
            self._command.send(key)
        self._command.send_complete()

class _ConsecutiveUniquer(object):

    _command = None
    _current = None

    def __init__(self, command):
        self._command = command

    def receive(self, object):
        if self._current != object:
            if self._current is not None:
                self._command.send(self._current)
            self._current = object

    def receive_complete(self):
        if self._current is not None:
            self._command.send(self._current)
        self._command.send_complete()

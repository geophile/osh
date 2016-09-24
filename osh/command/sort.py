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

"""C{sort [FUNCTION]}

Input objects are sorted before being written to output.  If
C{FUNCTION} is not provided then input objects are sorted using the
default ordering (i.e., based on the C{cmp} function).

If C{FUNCTION} is provided, then sorting is done by applying C{cmp} to
values obtained by applying C{FUNCTION} to the input objects.
"""

import osh.core

# CLI
def _sort():
    return _Sort()

# API
def sort(function = None):
    """Input objects are sorted before being written to output. If
    C{function} is not provided then input objects are sorted using the
    default ordering (i.e., based on the C{cmp} function).
    If C{function} is provided, then sorting is done by applying C{cmp} to
    values obtained by applying C{function} to the input objects.
    """
    args = []
    if function:
        args.append(function)
    return _Sort().process_args(*args)

class _Sort(osh.core.Op):

    _key = None
    _list = None


    # object interface

    def __init__(self):
        osh.core.Op.__init__(self, '', (0, 1))


    # BaseOp interface
    
    def doc(self):
        return __doc__

    def setup(self):
        args = self.args()
        if args.has_next():
            self._key = args.next_function()
        if args.has_next():
            self.usage()
        self._list = []
    
    def receive(self, object):
        self._list.append(object)
    
    def receive_complete(self):
        key = self._key
        if key:
            # Attach the keys, sort by the key, then detach the key.
            self._list = [(key(*object), object) for object in self._list]
            self._list.sort(lambda x, y: cmp(x[0], y[0]))
            self._list = [t[1] for t in self._list]
        else:
            self._list.sort()
        for object in self._list:
            self.send(object)
        self.send_complete()

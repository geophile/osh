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

"""C{tail N}

The last N items of the input sequence are passed on as output. All other input
is ignored. N must be an integer.

"""

import osh.core

# CLI
def _tail():
    return _Tail()

# API
def tail(n):
    """The last N items of the input sequence are passed on as output. All other input
    is ignored. N must be an integer.
    """
    return _Tail().process_args(n)

class _Tail(osh.core.Op):

    _n = None
    _tail = None
    _p = None
    _full = None


    # object interface

    def __init__(self):
        osh.core.Op.__init__(self, '', (1, 1))


    # BaseOp interface
    
    def doc(self):
        return __doc__

    def setup(self):
        args = self.args()
        self._n = args.next_int()
        self._tail = [None for i in xrange(self._n)]
        self._p = 0
        self._full = False

    def receive(self, object):
        if self._n > 0:
            self._tail[self._p] = object
            self._p += 1
            if self._p == self._n:
                self._full = True
                self._p = 0

    def receive_complete(self):
        tail = self._tail
        if self._full:
            for i in xrange(self._p, self._n):
                self.send(tail[i])
        for i in xrange(self._p):
            self.send(tail[i])
        self.send_complete()

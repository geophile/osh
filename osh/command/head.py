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

"""C{head N}

The first N items of the input sequence are passed on as output. All other input
is ignored. N must be an integer.

"""

import osh.core

# CLI
def _head():
    return _Head()

# API
def head(n):
    """The first N items of the input sequence are passed on as output. All other input
    is ignored. N must be an integer.
    """
    return _Head().process_args(n)

class _Head(osh.core.Op):

    _n = None
    _received = None


    # object interface

    def __init__(self):
        osh.core.Op.__init__(self, '', (1, 1))


    # BaseOp interface
    
    def doc(self):
        return __doc__

    def setup(self):
        args = self.args()
        self._n = args.next_int()
        self._received = 0

    def receive(self, object):
        self._received += 1
        delta = self._n - self._received
        if delta >= 0:
            self.send(object)

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

"""C{reverse}

Input objects are sent to the output stream in the opposite order, (last-in first-out).
"""

import osh.function
import osh.core

# CLI
def _reverse():
    return _Reverse()

# API
def reverse():
    """Input objects are sent to the output stream in the opposite order, (last-in first-out).
    """
    return _Reverse()

class _Reverse(osh.core.Op):

    _list = None


    # object interface

    def __init__(self):
        osh.core.Op.__init__(self, '', (0, 0))


    # BaseOp interface
    
    def doc(self):
        return __doc__

    def setup(self):
        self._list = []
    
    def receive(self, object):
        self._list.append(object)
    
    def receive_complete(self):
        self._list.reverse()
        for object in self._list:
            self.send(object)
        self.send_complete()

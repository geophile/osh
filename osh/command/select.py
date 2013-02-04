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

"""C{select FUNCTION}

C{FUNCTION} is applied to input objects. Objects for which C{FUNCTION}
evaluates to true are sent to the output stream.

B{Example}: For the input C{(1,), (2,), (3,), (4,)}, this command::

    select 'x: (x % 2) == 0'

generates the output C{(2,), (4,)}.
"""

import osh.function
import osh.core

# CLI
def _select():
    return _Select()

# API
def select(function):
    """Input objects for which C{function} evaluates to true are sent to the output stream.
    """
    return _Select().process_args(function)

class _Select(osh.core.Op):

    _function = None


    # object interface

    def __init__(self):
        osh.core.Op.__init__(self, '', (1, 1))


    # OshCommand interface
    
    def doc(self):
        return __doc__

    def setup(self):
        args = self.args()
        self._function = args.next_function()
        if self._function is None or args.has_next():
            self.usage()


    # Receiver interface
    
    def receive(self, object):
        # core ensures that we get a tuple (see wrap_if_necessary)
        if self._function(*object):
            self.send(object)

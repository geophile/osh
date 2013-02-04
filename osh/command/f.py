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

"""C{f FUNCTION}

The result obtained by applying C{FUNCTION} to an input sequence is
written as output.

B{Example}: If input contains the sequences C{(1, 2), (3, 4), (5, 6)}
then this command::

    f 'x, y: x + y'

generates the output C{(3,), (7,), (11,)}.
"""

import types

import osh.function
import osh.core

# CLI
def _f():
    return _F()

# API
def f(function):
    """The result obtained by applying C{FUNCTION} to an input sequence is
    written as output.
    """
    return _F().process_args(function)

# f can be used as a generator (function with no args) or
# downstream. That's why receive and execute are both defined.

class _F(osh.core.Generator):

    _function = None


    # object interface

    def __init__(self):
        osh.core.Generator.__init__(self, '', (1, 1))


    # BaseOp interface
    
    def doc(self):
        return __doc__

    def setup(self):
        args = self.args()
        self._function = args.next_function()
        if self._function is None or args.has_next():
            self.usage()

    def receive(self, object):
        # core ensures that we get a tuple (see wrap_if_necessary)
        self.send(self._function(*object))


    # Generator interface

    def execute(self):
        self.send(self._function())

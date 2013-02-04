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

"""C{gen [-p PAD] [COUNT [START]]}

Generate a sequence of C{COUNT} integers, starting at C{START}. If
C{START} is not specified, then the sequence starts at 0. If no
arguments are specified, then the sequence starts at 0 and does not
terminate.

If the C{-p} flag is specified, then the generated integers are
converted to strings and left padded so that each string contains
C{PAD} characters. C{len(str(COUNT + START))} must not exceed C{PAD}.
"""

import osh.core
import osh.args

Option = osh.args.Option

# CLI
def _gen():
    return _Gen()

# API
def gen(count = None, start = 0, pad = None):
    """Generate a sequence of C{count} integers, starting at C{start}. If no arguments
    are provided then the sequence starts at 0 and does not terminate. If C{pad} is
    specified, and is an integer, then the output values are strings, padded to the
    specified length. The length of the generated strings must not exceed C{pad}.
    """
    args = [count, start]
    if pad is not None:
        args.append(Option('-p', pad))
    return _Gen().process_args(*args)

class _Gen(osh.core.Generator):

    _count = None
    _start = None
    _format = None

    # object interface

    def __init__(self):
        osh.core.Generator.__init__(self, 'p:', (0, 2))

    # BaseOp interface
    
    def doc(self):
        return __doc__

    def setup(self):
        args = self.args()
        self._count = args.next_int()
        self._start = args.next_int()
        pad = args.int_arg('-p')
        if self._start is None:
            self._start = 0
        if pad is not None:
            self._format = '%%0%sd' % pad
            if len(str(self._count + self._start)) > pad:
                self.usage()
        if args.has_next():
            self.usage()


    # Generator interface
    
    def execute(self):
        if self._count is None:
            n = 0
            while True:
                self._format_and_send(n)
                n += 1
        else:
            for x in xrange(self._start, self._start + self._count):
                self._format_and_send(x)

    # For use by this class

    def _format_and_send(self, x):
        if self._format is None:
            self.send(x)
        else:
            self.send(self._format % x)
        

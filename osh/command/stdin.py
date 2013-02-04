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

"""For API usage only, (for CLI use C{cat ... | osh ^ ...} syntax instead.)
"""

import sys

import osh.core

# CLI
def _stdin():
    return _Stdin()

# API
def stdin():
    """Each line of input from stdin is written to the output stream.
    """
    return _Stdin()

class _Stdin(osh.core.Generator):

    _stdin = None


    # object interface

    def __init__(self):
        osh.core.Generator.__init__(self, '', (0, 0))


    # BaseOp interface
    
    def setup(self):
        pass

    def doc(self):
        return __doc__

    # Generator interface

    def execute(self):
        eof = False
        while not eof:
            line = sys.stdin.readline()
            if line:
                if line.endswith('\n'):
                    line = line[:-1]
                self.send(line)
            else:
                eof = True

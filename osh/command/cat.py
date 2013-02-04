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

r"""C{cat FILENAME}

Each line of the file named by C{FILENAME} is written to output.
Newline characters (\n) are omitted. The C{cat} command takes no
input.
"""

import sys

import osh.core

# CLI
def _cat():
    return _Cat()

# API
def cat(filename):
    r"""Each line of the file named by C{filename} is written to output.
    Newline characters (\n) are omitted. C{cat} takes no input.
    """
    return _Cat().process_args(filename)

class _Cat(osh.core.Generator):

    _filename = None


    # object interface

    def __init__(self):
        osh.core.Generator.__init__(self, '', (1, 1))


    # OshCommand interface
    
    def doc(self):
        return __doc__

    def setup(self):
        args = self.args()
        self._filename = args.next_string()
        if not self._filename:
            self.usage()


    # Generator interface

    def execute(self):
        file = open(self._filename, 'r')
        try:
            eof = False
            while not eof:
                line = file.readline()
                if line:
                    if line.endswith('\n'):
                        line = line[:-1]
                    self.send(line)
                else:
                    eof = True
        finally:
            file.close()

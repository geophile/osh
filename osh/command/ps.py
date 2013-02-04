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

"""C{ps [-o]}

Generates a stream of objects of type C{osh.process.Process}.

C{-o} omits the osh process itself from the process list.
"""

import os
import os.path

import osh.core
import osh.process

Option = osh.args.Option

# CLI
def _ps():
    return _Ps()

# API
def ps(omitself = True):
    """Generates a stream of objects of type C{osh.process.Process}. The osh process
    itself is omitted if C{omitself} is true.
    """
    args = []
    if omitself:
        args.append(Option('-o'))
    return _Ps().process_args(*args)

class _Ps(osh.core.Generator):

    _omit_self = None

    # object interface

    def __init__(self):
        osh.core.Generator.__init__(self, 'o', (0, None))

    # BaseOp interface
    
    def doc(self):
        return __doc__

    def setup(self):
        self._omit_self = self.args().flag('-o')

    # Generator interface
    
    def execute(self):
        this_pid = os.getpid()
        for process in osh.process.processes():
            if not self._omit_self or process.pid != this_pid:
                self.send(process)

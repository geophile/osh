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

"""C{version}

The osh version number is sent to the output stream.
"""

import osh.config
import osh.core

# CLI
def _version():
    return _Version()

# API
def version():
    """The osh version number is sent to the output stream.
    """
    return _Version()

class _Version(osh.core.Generator):

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
        version = osh.config.OSH_VERSION
        if osh.config.OSH_SUBVERSION:
            version += '/' + osh.config.OSH_SUBVERSION
        self.send(version)

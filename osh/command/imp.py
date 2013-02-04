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

"""C{import MODULE_NAME ...}

Imports modules for use by subsequent commands. Input objects are
passed to the output stream.
"""

import sys

import osh.args
import osh.core

# CLI
def _imp():
    return _Imp()

# API
def imp(*module_names):
    """Imports modules for use by subsequent commands. Input objects are passed through to
    the output stream.
    """
    return _Imp().process_args(*module_names)

class _Imp(osh.core.Generator):

    # object interface

    def __init__(self):
        osh.core.Op.__init__(self, '', (1, None))


    # BaseOp interface
    
    def doc(self):
        return __doc__

    def setup(self):
        args = self.args()
        for module_name in args.remaining():
            exec('import %s' % module_name)
            dot = module_name.find('.')
            if dot < 0:
                top_module_name = module_name
            else:
                top_module_name = module_name[:dot]
            osh.core.add_to_namespace(top_module_name, locals()[top_module_name])
    
    def receive(self, object):
        self.send(object)


    # Generator interface

    def execute(self):
        self.send(tuple()) # Have to send something

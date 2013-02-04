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

"""C{py PYTHON_CODE}

C{PYTHON_CODE} is executed, and any variables defined are available to
subsequent commands in the same command line.

B{Example}::

    osh py 'a = 123; b = 456' ^ f '(a, b)' $

This command generates the output C{'(123, 456)'}.

In addition to executing the specified code, input objects are passed
to the output stream.
"""

import sys

import osh.args
import osh.core

# CLI
def _py():
    return _Py()

# API
def py(python_code):
    """C{python_code} is executed. Any symbols defined by the execution of this
    code are available to subsequent osh commands. Input objects are passed to
    the output stream.
    """
    return _Py().process_args(python_code)

class _Py(osh.core.Op):

    # object interface

    def __init__(self):
        osh.core.Op.__init__(self, '', (1, 1))


    # BaseOp interface
    
    def doc(self):
        return __doc__

    def setup(self):
        code = self.args().next_string()
        before = globals().copy()
        exec code in globals()
        after = globals()
        # Put new symbols in function.defined_by_osh
        for key, value in after.iteritems():
            if key not in before:
                osh.core.add_to_namespace(key, value)
    
    def receive(self, object):
        self.send(object)


    # Generator interface

    def execute(self):
        self.send(tuple()) # Have to send something

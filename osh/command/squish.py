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

"""C{squish [BINARY_FUNCTION ...]}

Each input sequence is reduced to a single value, using C{BINARY_FUNCTION}
to combine the values. C{BINARY_FUNCTION} is a binary function that can be
used for reduction, e.g. C{+}, C{*}, C{max}, C{min}, but not C{-} or
C{/}.

B{Example}: If one of the inputs is the list C{[1, 2, 3, 4]}, then::

    squish +

will generate C{10} (= C{1 + 2 + 3 + 4}).

The result is exactly equivalent to what would be produced by using
the Python function C{map}, e.g.::

    map 'list: squish(lambda a, b: a + b, list)'

If input sequences contain nested sequences, then multiple C{BINARY_FUNCTION}s
can be provided, to do multiple reductions at once. For example, if
one input sequence is C{[[10, 20, 30], [1, 100, 1000], [111, 222, 333]]}
then::

    squish + max min

will produce C{[122, 222, 30]}. C{122} is C{10 + 1 + 111}, C{222} is C{max(20, 100, 222)}, and
C{30} is C{min(30, 1000, 333)}.

If no C{BINARY_FUNCTION} is provided, then C{+} is assumed.
"""

import types

import osh.core
import osh.function

create_function = osh.function._create_function

# CLI
def _squish():
    return _Squish()

# API
def squish(*squish_ops):
    """Each input sequence is reduced to a single value. Elements
    of the input sequence are combined using a C{squish_op}, a binary function
    that can be used for reduction, i.e. a binary associative function such as addition,
    but not subtraction, (because x + y = y + x, but x - y != y - x).
    If input sequences contain nested sequences, then multiple C{squish_op}s
    can be provided, to do multiple reductions at once. The squish_op can be a function-valued
    expression, a string function expression (e.g. C{'x, y: x + y'}), or a string describing
    a binary associative operator, specifically one of: C{+, *, ^, &, |, and, or}.
    """
    return _Squish().process_args(*squish_ops)

class _Squish(osh.core.Op):

    _squisher = None


    # object interface

    def __init__(self):
        osh.core.Op.__init__(self, '', (0, None))


    # BaseOp interface
    
    def doc(self):
        return __doc__

    def setup(self):
        args = self.args()
        squish_ops = []
        while args.has_next():
            arg = args.next()
            op = create_function(arg)
            squish_ops.append(op)
        if len(squish_ops) == 0:
            squish_ops.append(create_function(lambda x, y: x + y))
        if len(squish_ops) == 1:
            self._squisher = _object_squisher(squish_ops[0])
        else:
            self._squisher = _sequence_squisher(squish_ops)

    def receive(self, object):
        squished = self._squisher(object)
        self.send(squished)

def _object_squisher(op):
    return lambda input: reduce(op, input)

def _sequence_squisher(ops):
    def all_ops(x, y):
        return tuple([ops[i](x[i], y[i]) for i in xrange(len(ops))])
    return lambda input: reduce(all_ops, input)

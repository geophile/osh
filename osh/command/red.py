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

"""C{red -r [BINARY_FUNCTION ...]}

Aggregates (reduces) objects from the input stream in a simpler but less general
way than the C{agg} command.

A C{BINARY_FUNCTION} takes two inputs and produces one output. Binary operators
and user-defined functions can be used as C{BINARY_FUNCTION}s. Given a sequence
of inputs such as C{(1,), (2,), (3,)}, C{red} can be used to find the sum::

    ... ^ red +

yields C{(6,)}. If each input sequence contains multiple values, then multiple
C{BINARY_FUNCTION}s can be provided. For example, to find the sums of the first
10 integers, the sum of their squares, and the sum of their cubes::

    osh gen 10 ^ f 'x: (x, x**2, x**3)' ^ red + + + $

which yields the output C{(45, 285, 2025)}.

If C{.} is provided as one of the C{BINARY_FUNCTION}s, then that value is not aggregated.
Instead, aggregation is done for the groups defined by the indicated elements. For example,
suppose the input sequence is::

    (1, 10, 5, 100)
    (1, 10, 6, 200)
    (1, 11, 4, 100)
    (1, 11, 3, 200)
    (2, 20, 8, 100)
    (2, 20, 9, 200)
    (2, 20, 10, 300)
    (3, 30, 5, 100)

If this sequence is piped to this invocation of C{red}::

    red . . + +

Then the output sequence would be::

    (1, 10, 11, 300)
    (1, 11, 7, 300)
    (2, 20, 17, 300)
    (3, 30, 5, 100)

The two C{.}s, in the first two positions, mean that the groups used for aggregation
are C{(1, 10)}, C{(1, 11)}, C{(2, 20)}, and C{(3, 30)}. The
C{(1, 10)} group has two rows, C{(1, 10, 5, 100)},
and C{(1, 10, 6, 200)}. The two C{+}s mean that the items in the last two fields should be summed.
Adding the items in the third position, 5 + 6 = 11; and in the last position, 100 + 200 = 300.

If the C{-r} flag is specified, then one output object is generated for each input object;
the output object contains the current accumulated values. The accumulator appears
in the output row before the inputs. For example, if the input stream contains C{(1,), (2,), (3,)},
then the running total can be computed as follows::

    ... ^ red -r + ^ ...

The output stream would be C{(1, 1), (3, 2), (6, 3)}. In the last output object, C{6} is the sum
of the current input (C{3}) and all preceding inputs (C{1, 2}).

The C{-r} flag can also be used with grouping. For example, if the input objects are
C{('a', 1), ('a', 2), ('b', 3), ('b', 4)}, then the running totals for the strings would
be computed as follows::

    ... ^ red -r -g 'x, y: x' 0 'sum, x, y: sum + y' ^ ...

The output stream would be C{(1, 'a', 1), (3, 'a', 2), (3, 'b', 3), (7, 'b', 4)}.
"""

import osh.core
import osh.args
import osh.function
import agg

create_function = osh.function._create_function
Option = osh.args.Option
_GroupingAggregate = agg._GroupingAggregate
_NonGroupingAggregate = agg._NonGroupingAggregate

# CLI
def _red():
    return _Red()

# API
def red(binary_functions, running = False):
    """C{binary_functions} is a sequence. Each element of C{binary_functions} is
    either None or a binary function.
    If no elements are C{None}, then the binary function in position C{i} is used
    to reduce the values in element C{i} of the input sequences. If there are
    C{None} values, then these are used to define groups of inputs, partitioning
    by the values in the indicated columns. The remaining binary functions then compute
    reductions within each group. If C{running} is C{False} then there is one output
    tuple in the absence of grouping; otherwise there is one tuple output per group.
    If C{running} is {True}, then the aggregate value computed so far is written
    out for each input, i.e., the output contains "running totals". In this case,
    the aggregate value appears before the input values.
    """
    if not (isinstance(binary_functions, list) or
            isinstance(binary_functions, tuple)):
        binary_functions = [binary_functions]
    args = [f for f in binary_functions]
    if running:
        args.append(Option('-r'))
    return _Red().process_args(*args)

class _Red(osh.core.Op):

    _aggregate = None
    
    # object interface

    def __init__(self):
        osh.core.Op.__init__(self, 'r', (1, None))


    # BaseOp interface

    def doc(self):
        return __doc__

    def setup(self):
        args = self.args()
        running = args.flag('-r')
        if running is None:
            running = False
        functions = args.remaining()
        # A "group" position contains a dot, used to indicate grouping.
        # A "data" position does not contain a dot; it contains data that will be aggregated.
        group_positions = []
        data_positions = []
        for p in xrange(len(functions)):
            f = functions[p]
            if f == '.' or f is None:
                group_positions.append(p)
            else:
                data_positions.append(p)
        n_group = len(group_positions)
        n_data = len(data_positions)
        functions = [create_function(functions[p]) for p in data_positions]
        initial_value = (None,) * n_data
        if n_group == 0:
            def aggregator(*t):
                if t[:n_data] == initial_value:
                    # all None => first item, need to initialize accumulator
                    accumulator = t[-n_data:]
                else:
                    accumulator = tuple([functions[p](t[p], t[n_data + p])
                                         for p in xrange(n_data)])
                return accumulator
            self._aggregate = _NonGroupingAggregate(self,
                                                    running,
                                                    initial_value,
                                                    aggregator)
        else:
            def grouper(*t):
                return tuple([t[p] for p in group_positions])
            def aggregator(*t):
                if reduce(lambda r, x: r and x is None, t[:n_data], True):
                    # all None => first item, need to initialize accumulator
                    accumulator = tuple([t[n_data + data_positions[p]]
                                         for p in xrange(n_data)])
                else:
                    accumulator = tuple([functions[p](t[p], t[n_data + data_positions[p]])
                                         for p in xrange(n_data)])
                return accumulator
            self._aggregate = _GroupingAggregate(self,
                                                 running,
                                                 grouper,
                                                 initial_value,
                                                 aggregator)

    def receive(self, object):
        self._aggregate.receive(object)

    def receive_complete(self):
        self._aggregate.receive_complete()


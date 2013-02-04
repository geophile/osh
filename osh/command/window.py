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

"""C{window PREDICATE}

C{window -o WINDOW_SIZE}

C{window -d WINDOW_SIZE}
    
Groups of consecutive input objects are formed into tuples which are
passed to the output stream. The objects are grouped in one of two
mechanisms.

1) A new group is started on the first input object, and for any
subsequent object for which C{PREDICATE} returns true. For example, if
the input stream contains the integers C{1, 2, 3, ...}, then::

    window 'n: n % 3 == 2'

yields as output::

    ((1,),)
    ((2,), (3,), (4,))
    ((5,), (6,), (7,))
    ((8,), (9,), (10,))
    ...

I.e., a new tuple is started for each integer n such that n % 3 = 2.

2) Groups have a fixed number of objects. The C{-o} and C{-d} flags
specify C{WINDOW_SIZE}, the number of objects in the groups.  C{-o}
specifies I{overlapping} windows, in which each input object begins a
new list containing C{WINDOW_SIZE} items. Groups may be padded with
C{None} values to ensure that the group's size is C{WINDOW_SIZE}.
    
B{Example}: For input C{0, 1, ..., 9}, C{window -o 3} yields these
tuples::
    
    ((0,), (1,), (2,))
    ((1,), (2,), (3,))
    ((2,), (3,), (4,))
    ((3,), (4,), (5,))
    ((4,), (5,), (6,))
    ((5,), (6,), (7,))
    ((6,), (7,), (8,))
    ((7,), (8,), (9,))
    ((8,), (9,), (None,))
    ((9,), (None,), (None,))

C{-d} specifies I{disjoint} windows, in which each input object
appears in only one group. A new group is started every C{WINDOW_SIZE}
objects. The last window may be padded with (None,) to ensure that it
has C{WINDOW_SIZE} elements.
    
B{Example}: For input C{0, 1, ..., 9}, C{window -d 3} yields these
tuples::
    
    ((0,), (1,), (2,))
    ((3,), (4,), (5,))
    ((6,), (7,), (8,))
    ((9,), (None,), (None,))
"""

import types

import osh.args
import osh.core

Option = osh.args.Option

# CLI
def _window():
    return _Window()

# API
def window(predicate = None, disjoint = None, overlap = None):
    """Groups of consecutive input objects are formed into tuples which
    are passed to the output stream. Only one of C{predicate},
    C{disjoint}, ant C{overlap} may be specified. If C{predicate}, a
    function returning a boolean, is specified, then a new group of
    objects is started for the first input, and subsequently for every
    input object which causes C{predicate} to return true. If
    C{disjoint}, an integer, is specified, then the input is broken
    into disjoint groups of C{disjoint} objects each. If C{overlap},
    an int, is specified, then each input object begins a group of
    C{overlap} objects. For both C{disjoint} and C{overlap}, groups
    may be padded with C{None} values to form groups of the required
    size.    
    """
    arg = predicate
    if not arg and disjoint:
        arg = Option('-d', disjoint)
    if not arg and overlap:
        arg = Option('-o', overlap)
    return _Window().process_args(arg)

class _Window(osh.core.Op):

    _window_generator = None


    # object interface

    def __init__(self):
        osh.core.Op.__init__(self, 'o:d:', (0, 1))


    # BaseOp interface
    
    def doc(self):
        return __doc__

    def setup(self):
        args = self.args()
        overlap = args.int_arg('-o')
        disjoint = args.int_arg('-d')
        if overlap is not None and disjoint is not None:
            self.usage()
        elif overlap is not None:
            self._window_generator = _OverlapWindow(overlap)
        elif disjoint is not None:
            self._window_generator = _DisjointWindow(disjoint)
        else:
            predicate = args.next_function()
            self._window_generator = _PredicateWindow(predicate)

    def receive(self, object):
        self._window_generator.process(object, self)

    def receive_complete(self):
        self._window_generator.finish(self)
        self.send_complete()

class _OverlapWindow(object):

    _window_size = None
    _window = None

    def __init__(self, window_size):
        self._window_size = window_size
        self._window = []

    def process(self, object, op):
        if len(self._window) == self._window_size:
            self._window = self._window[1:]
        self._window.append(object)
        if len(self._window) == self._window_size:
            op.send(self._window)

    def finish(self, op):
        padding = (None,)
        if len(self._window) < self._window_size:
            while len(self._window) < self._window_size:
                self._window.append(padding)
            op.send(self._window)
        else:
            for i in xrange(self._window_size - 1):
                self._window = self._window[1:]
                self._window.append(padding)
                op.send(self._window)

class _DisjointWindow(object):

    _window_size = None
    _window = None

    def __init__(self, window_size):
        self._window_size = window_size
        self._window = []

    def process(self, object, op):
        self._window.append(object)
        if len(self._window) == self._window_size:
            op.send(self._window)
            self._window = []

    def finish(self, op):
        if len(self._window) == 0:
            # Last window was complete
            pass
        else:
            padding = (None,)
            while len(self._window) < self._window_size:
                self._window.append(padding)
            op.send(self._window)

class _PredicateWindow(object):
    
    _predicate = None
    _window = None

    def __init__(self, predicate):
        self._predicate = predicate
        self._window = []

    def process(self, object, op):
        if self._predicate(*object):
            if len(self._window) > 0:
                op.send(self._window)
                self._window = []
        self._window.append(object)

    def finish(self, op):
        op.send(self._window)

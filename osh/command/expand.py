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

"""C{expand [POSITION]}

Receives a stream of sequences as input. If C{POSITION} is omitted, then
each item of the sequence is generated as a separate 1-tuple in the
output stream.

B{Example}: If the input contains these sequences::

    ('a', 'b')
    ('c', 'd')

then C{expand} generates this output::
    ('a',)
    ('b',)
    ('c',)
    ('d',)

If C{POSITION} is specified, then each input sequence is used to generate
zero or more output sequences. In each output sequence, the item at the
selected position is replaced by one component of the selected object.

The types that can be expanded are C{list}, C{tuple}, C{generator},
and C{osh.file.File}. Expansion of a C{osh.file.File}
yields each line of the named file.

B{Example}: If the input contains these sequences::

    ('a', [1, 2, 3], 'x')
    ('b', [4, 5], 'y')
    ('c', [], 'z')

then C{expand 1} generates this output::

    ('a', 1, 'x')
    ('a', 2, 'x')
    ('a', 3, 'x')
    ('b', 4, 'y')
    ('b', 5, 'y')

Note that an empty nested sequence results in no output, (as for
C{('c', [], 'z')}.)
"""

import types

import osh.core
import osh.file

# CLI
def _expand():
    return _Expand()

# API
def expand(position = None):
    """Flattens an input sequence by generating output sequences in which an interior element
    is expanded. If C{position} is omitted, then each element of the input sequence is generated
    as a separate 1-tuples. If C{position} is specified, then the item at the given position
    is expanded. If the element being expanded is a string, then the string is interpreted
    as a filename, and the expansion yields each line of the file in turn.
    """
    args = []
    if position is not None:
        args.append(position)
    return _Expand().process_args(*args)

class _Expand(osh.core.Op):

    _expander = None


    # object interface

    def __init__(self):
        osh.core.Op.__init__(self, None, (0, 1))
    

    # BaseOp interface
    
    def doc(self):
        return __doc__

    def setup(self):
        args = self.args()
        position = args.next_int()
        if position is not None and args.has_next():
            self.usage()
        if position is None:
            self._expander = _SequenceExpander(self)
        else:
            self._expander = _ComponentExpander(self, position)
    
    def receive(self, sequence):
        self._expander.expand(sequence)

class _Expander(object):

    _command = None

    def __init__(self, command):
        self._command = command

    def expand(self, sequence):
        assert False

    def contents(self, object):
        contents_generator = self._expand_as_file(object)
        if not contents_generator:
            contents_generator = self._expand_as_sequence(object)
        if not contents_generator:
            raise _NotExpandableException(object)
        return contents_generator

    def _expand_as_file(self, object):
        assert False

    def _expand_as_sequence(self, object):
        if (isinstance(object, tuple) or
            isinstance(object, list) or
            isinstance(object, types.GeneratorType)):
            return self._expand_sequence(object)
        else:
            return None

    def _expand_file(self, f):
        if isinstance(f, osh.file.File):
            filename = f.abspath
        else:
            filename = f
        file = open(filename, 'r')
        eof = False
        while not eof:
            line = file.readline()
            if line:
                if line.endswith('\n'):
                    line = line[:-1]
                yield line
            else:
                eof = True
        file.close()

    def _expand_sequence(self, sequence):
        for object in sequence:
            yield object

class _SequenceExpander(_Expander):

    def __init__(self, command):
        _Expander.__init__(self, command)

    def expand(self, sequence):
        for object in self.contents(sequence):
            self._command.send(object)

    def _expand_as_file(self, object):
        # Expand as file if object is a sequence of len 1,
        # containing a File.
        if ((isinstance(object, tuple) or isinstance(object, list)) and len(object) == 1):
            object = object[0]
        if isinstance(object, osh.file.File):
            return self._expand_file(object)
        else:
            return None

class _ComponentExpander(_Expander):

    _position = None

    def __init__(self, command, position):
        _Expander.__init__(self, command)
        self._position = position

    def expand(self, sequence):
        pre = sequence[:self._position]
        if self._position == -1:
            post = tuple()
        else:
            post = sequence[(self._position + 1):]
        contents = self.contents(sequence[self._position])
        for object in contents:
            output = pre + (object,) + post
            self._command.send(output)

    def _expand_as_file(self, sequence):
        # Expand as file if item at position is a File.
        if isinstance(sequence, osh.file.File):
            return self._expand_file(sequence)
        else:
            return None

class _NotExpandableException(Exception):

    _object = None

    def __init__(self, object):
        self._object = object

    def __str__(self):
        return 'Object of type %s cannot be expanded: %s' % (type(self._object), self._object)

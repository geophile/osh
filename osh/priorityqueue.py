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

import threading

# import trace
# trace.on('/tmp/trace.txt')
# trace = trace.trace

class SpecialValue(object):

    _name = None
    _value = None

    def __init__(self, name, value):
        self._name = name
        self._value = value

    def __repr__(self):
        return self._name

    def __lt__(self, other):
        return self._value < other._value

    def __le__(self, other):
        return self._value <= other._value

    def __gt__(self, other):
        return self._value > other._value

    def __ge__(self, other):
        return self._value >= other._value

    def __eq__(self, other):
        return self._value == other._value

    def __ne__(self, other):
        return self._value != other._value

MINUS_INFINITY = SpecialValue('MINUS_INFINITY', 0)
INFINITY = SpecialValue('INFINITY', 1)
DEBUG = True
WRITE_BUFFER_CAPACITY = 1000
LOCK_WAIT_TIME = 1.0

def _describe_list(x):
    n = len(x)
    if n == 0:
        boundaries = ''
    elif n == 1:
        boundaries = str(x[0])
    elif n == 2:
        boundaries = '%s, %s' % (x[0], x[1])
    else:
        boundaries = '%s .. %s' % (x[0], x[-1])
    return '%s[%s]' % (len(x), boundaries)

class PriorityQueue(object):

    _nodes = None
    _inputs = None
    _first_input = None
    _key = None
    
    def __init__(self, key, inputs):
        self._key = key
        self._inputs = inputs
        # Compute number of leaves and nodes
        leaves = 1
        while leaves < self._inputs:
            leaves *= 2
        nodes = 2 * leaves - 1
        # Set up to create tree
        self._first_input = leaves - 1
        self._nodes = []
        # Create interior nodes
        for i in xrange(self._first_input):
            self._nodes.append(_InteriorNode(self))
        # Create input nodes
        for i in xrange(self._inputs):
            self._nodes.append(_InputNode(self, i))
        # Create filler nodes
        while len(self._nodes) < nodes:
            self._nodes.append(_FillerNode(self))
        # Starting with filler nodes, propagate INFINITY up the tree. In general, if self is
        # INFINITY and self has a left sibling, and the left sibling is INFINITY, then
        # propagate up.
        for i in xrange(self._first_input + self._inputs, len(self._nodes)):
            node = self._nodes[i]
            while ((not node.is_root) and
                   node.parent.right is node and
                   type(node.parent.left) is not _InputNode and # can't check input node content
                                                                # before loading.
                   node.parent.left.content is INFINITY):
                node = node.parent
                node.content = INFINITY

    def __repr__(self):
        return 'PriorityQueue<%s>' % id(self)

    def __iter__(self):
        # Promote until root is not MINUS_INFINITY. 
        root = self._nodes[0]
        while root.content is MINUS_INFINITY:
            root.promote()
        output = root.content
        while output is not INFINITY:
            # trace('%s: yielding %s' % (self, output))
            yield output
            root.promote()
            output = root.content

    def add(self, index, object):
        # trace('%s: add to %s: %s' % (self, index, object))
        self._nodes[self._first_input + index].add(object)

    def done(self, index):
        self.add(index, INFINITY)

    def dump(self, label = None):
        if label:
            label = [label]
        else:
            label = []
        return '\n'.join(label + ['%s: %s' % (node._id, str(node)) for node in self._nodes])


class _Node(object):

    _priority_queue = None
    _key = None
    _id = None
    
    def __init__(self, priority_queue):
        self._priority_queue = priority_queue
        self._key = priority_queue._key
        self._id = len(priority_queue._nodes)

    def __repr__(self):
        return '%s#%s(%s)' % (self.node_type(), self._id, self.content)

    def _compare(self, x, y):
        if type(x) is type(y):
            # Both SpecialValue or both not SpecialValue
            if isinstance(x, SpecialValue):
                c = cmp(x, y)
            else:
                key = self._key
                kx = key(x)
                ky = key(y)
                c = cmp(kx, ky)
        elif x is INFINITY:
            c = 1
        elif y is INFINITY:
            c = -1
        elif x is MINUS_INFINITY:
            c = -1
        elif y is MINUS_INFINITY:
            c =  1
        else:
            assert False, (type(x), x, type(y), y)
        return c

    is_root = property(lambda self: self._id == 0)
    parent = property(lambda self: self._priority_queue._nodes[(self._id - 1) / 2])
    left = property(lambda self: self._priority_queue._nodes[self._id * 2 + 1])
    right = property(lambda self: self._priority_queue._nodes[self._id * 2 + 2])

    def promote(self):
        assert False, type(self)

    def node_type(self):
        assert False

class _InteriorNode(_Node):

    _content = None

    def __init__(self, priority_queue):
        _Node.__init__(self, priority_queue)
        self._content = MINUS_INFINITY

    def node_type(self):
        return 'interior'

    def promote(self):
        key = self._key
        c = self._compare(self.left.content, self.right.content)
        if c <= 0:
            self.content = self.left.content
            self.left.promote()
        else:
            self.content = self.right.content
            self.right.promote()

    def _get_content(self):
        return self._content
        
    def _set_content(self, content):
        self._content = content

    content = property(_get_content, _set_content)

class _InputNode(_Node):

    _source = None # int
    _done = None
    _buffer = None # _Buffer
    
    def __init__(self, priority_queue, source):
        _Node.__init__(self, priority_queue)
        self._done = False
        self._source = source
        self._buffer = _Buffer(self)

    def __repr__(self):
        # reporting content for input nodes is dangerous
        return '%s#%s(?)' % (self.node_type(), self._id)

    def node_type(self):
        return 'input'

    def add(self, input):
        if self._done:
            raise PriorityQueueInputClosedException(self._source)
        self._buffer.add(input)

    def done(self):
        self._done = True

    def promote(self):
        self._buffer.next()

    content = property(lambda self: self._buffer.current())
    source = property(lambda self: self._source)

class _FillerNode(_Node):

    def __init__(self, priority_queue):
        _Node.__init__(self, priority_queue)

    def node_type(self):
        return 'filler'

    content = property(lambda self: INFINITY)

class _Buffer(object):

    _lock = None
    _input_node = None
    _read = None # list of objects
    _read_position = None # position of current item in _read
    _write = None # list of objects
    _last_input = None
    _done = None

    def __init__(self, input_node):
        self._lock = threading.Condition()
        self._input_node = input_node
        self._read = []
        self._read_position = 0
        self._write = []
        self._last_input = None
        self._done = False
        # trace('%s: created' % self)

    def __repr__(self):
        buffer = ['buffer<']
        buffer.append(str(id(self)))
        buffer.append('>#')
        buffer.append(str(self._input_node.source))
        buffer.append('(pq:')
        buffer.append(str(self._priority_queue))
        buffer.append(', read:')
        buffer.append(_describe_list(self._read))
        buffer.append(', write: ')
        buffer.append(_describe_list(self._write))
        buffer.append(')')
        return ''.join(buffer)

    def current(self):
        if self._done:
            current = INFINITY
        else:
            self._ensure_read_not_empty()
            current = self._read[self._read_position]
            if current is INFINITY:
                self._done = True
        return current

    def _write_blocked(self):
        return len(self._write) == WRITE_BUFFER_CAPACITY

    def _read_blocked(self):
        write_buffer_size = len(self._write)
        # trace('%s: write_buffer_size = %s, last input: %s' % (self, write_buffer_size, self._last_input))
        return (write_buffer_size < WRITE_BUFFER_CAPACITY and
                (write_buffer_size == 0 or self._last_input is not INFINITY))

    def _ensure_read_not_empty(self):
        if self._read_position == len(self._read):
            self._lock.acquire()
            while self._read_blocked():
                # trace('%s: read blocked' % self)
                self._lock.wait(LOCK_WAIT_TIME)
            # trace('%s: read unblocked' % self)
            self._read = self._write
            self._read_position = 0
            self._write = []
            self._lock.notify()
            self._lock.release()

    _priority_queue = property(lambda self: self._input_node._priority_queue)

    def add(self, input):
        # trace('%s: add %s' % (self, input))
        if (self._last_input is not None) and (self._input_node._compare(input, self._last_input) < 0):
            raise PriorityQueueInputOrderingException(self._input_node, input, self._last_input)
        if self._write_blocked():
            self._lock.acquire()
            # If reader is blocking, then release it now. No point waiting for the write
            # to be able to proceed.
            self._lock.notify()
            while self._write_blocked():
                # trace('%s: write blocked' % self)
                self._lock.wait(LOCK_WAIT_TIME)
            # trace('%s: write unblocked' % self)
            self._lock.notify()
            self._lock.release()
        self._write.append(input)
        self._last_input = input
        if input is INFINITY:
            # Don't keep reader waiting. This is like the notification to the reader when the writer
            # is blocked. This case needs special handling because the buffer probably won't be full
            # once INFINITY has arrived.
            self._lock.acquire()
            self._lock.notify()
            self._lock.release()

    def next(self):
        if self._done:
            output = INFINITY
        else:
            self._ensure_read_not_empty()
            output = self._read[self._read_position]
            self._read[self._read_position] = None
            self._read_position += 1
        return output

class PriorityQueueInputClosedException(Exception):

    def __init__(self, source):
        Exception.__init__(
            self,
            'Attempt to call add or done on input stream %s after calling done' % source)

class PriorityQueueInputOrderingException(Exception):

    def __init__(self, source, input, last_input):
        Exception.__init__(
            self,
            'Incorrectly ordered input for input stream %s: %s after %s' %
            (source, input, last_input))

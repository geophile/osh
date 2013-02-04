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

import sys
import threading

import osh.args
import osh.core
import osh.priorityqueue

# import osh.trace
# osh.trace.on('/tmp/trace.txt')
# trace = osh.trace.trace

Option = osh.args.Option

# CLI
def _merge():
    return _Merge()

# API
def merge(key = 'x: x'):
    """TBD
    """
    return _Merge().process_args(key)

class _Merge(osh.core.Op):

    _key = None

    def __init__(self):
        osh.core.Op.__init__(self, '', (1, 1))

    def create_command_state(self, oshthreads):
        return _MergeState(oshthreads)
    
    def setup(self):
        key_fcn = self.args().next_function()
        # Merge key function must be applied to tuple without threadid (in position 0).
        if key_fcn:
            self._key = lambda x: key_fcn(*x[1:])
        else:
            self._key = None
        # Any thread's merge object can be used to initialize command state.
        self.command_state().setup(self)

    def receive(self, object):
        # trace('%s: receive %s' % (self, object))
        self.command_state().add(self.thread_state, object)
        # trace('%s: receive %s done' % (self, object))

    def receive_complete(self):
        # trace('%s: receive_complete' % self)
        self.command_state().done(self.thread_state)
        # trace('%s: receive_complete done' % self)

    key = property(lambda self: self._key)

class _MergeState(osh.priorityqueue.PriorityQueue):

    _oshthreads = None
    _thread_to_input = None
    _merger = None
    _consumer = None
    
    def __init__(self, oshthreads):
        self._oshthreads = oshthreads
        self._thread_to_source = {}
        source = 0
        for thread in oshthreads:
            self._thread_to_source[thread.state] = source
            source += 1

    def __repr__(self):
        return 'mergestate<%s>' % id(self)

    def setup(self, merge_op):
        if self._merger  is None:
            if merge_op._key:
                self._merger = _PriorityQueueMerger(merge_op, len(self._oshthreads))
            else:
                self._merger = _VanillaMerger(merge_op, len(self._oshthreads))

    def add(self, threadid, object):
        self._merger.add(self._thread_to_source[threadid], object)

    def done(self, threadid):
        self._merger.done(self._thread_to_source[threadid])

class _Merger(object):

    _merge_op = None
    
    def __init__(self, merge_op):
        self._merge_op = merge_op
    
    def add(self, source, object):
        assert False

    def done(self, source):
        assert False

class _VanillaMerger(_Merger):

    _lock = None
    _active_sources = None

    def __init__(self, merge_op, n_sources):
        _Merger.__init__(self, merge_op)
        self._lock = threading.RLock()
        self._active_sources = n_sources
    
    def add(self, source, object):
        self._merge_op.send(object)

    def done(self, source):
        self._lock.acquire()
        self._active_sources -= 1
        if self._active_sources == 0:
            self._merge_op.send_complete()
        self._lock.release()

class _PriorityQueueMerger(_Merger):

    _priority_queue = None
    _consumer = None
    _n_sources = None
    _n_done = None
    
    def __init__(self, merge_op, n_sources):
        _Merger.__init__(self, merge_op)
        self._priority_queue = osh.priorityqueue.PriorityQueue(merge_op.key, n_sources)
        self._n_sources = n_sources
        self._n_done = 0
        self._consumer = _PriorityQueueConsumer(merge_op, self._priority_queue)
        self._consumer.start()

    def add(self, source, object):
        # trace('%s: merge %s source %s, add %s' % (self, self._merge_op, source, object))
        self._priority_queue.add(source, object)
        # trace('%s: merge %s source %s, add %s finished' % (self, self._merge_op, source, object))

    def done(self, source):
        # trace('%s: merge %s source %s, done' % (self, self._merge_op, source))
        self._priority_queue.done(source)
        # trace('%s: merge %s source %s, done finished' % (self, self._merge_op, source))
        self._n_done += 1
        if self._n_done == self._n_sources:
            while self._consumer.isAlive():
                self._consumer.join(1.0)
        
class _PriorityQueueConsumer(threading.Thread):

    _merge_op = None
    _priority_queue = None
    
    def __init__(self, merge_op, priority_queue):
        threading.Thread.__init__(self)
        self._merge_op = merge_op
        self._priority_queue = priority_queue
        self.setDaemon(False)

    def run(self):
        # trace('%s: run' % self)
        merge = self._merge_op
        for x in self._priority_queue:
            # trace('%s: send %s' % (self, x))
            merge.send(x)
            # trace('%s: send %s done' % (self, x))
        # trace('%s: send complete' % self)
        merge.send_complete()

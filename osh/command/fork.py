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

"""For API usage only, (for CLI use C{osh @FORK [ ... ]} syntax instead.)
"""

import types

import osh.args
import osh.cluster
import osh.core
import osh.error
import osh.function
import osh.oshthread
import osh.spawn
import osh.util
import merge

LineOutputConsumer = osh.spawn.LineOutputConsumer
ObjectInputProvider = osh.spawn.ObjectInputProvider
ObjectOutputConsumer = osh.spawn.ObjectOutputConsumer
Spawn = osh.spawn.Spawn
Option = osh.args.Option
create_function = osh.function._create_function

# CLI
def _fork():
    return _Fork()

# API
def fork(threadgen, command, merge_key = None):
    """Creates threads and executes C{command} on each. The number of threads is determined
    by C{threadgen}. If C{threadgen} is an integer, then the specified number of threads is created,
    and each thread has an integer label, from 0 through C{threadgen} - 1. If C{threadgen} is
    a sequence, then for each element in the sequence, a thread is created, labelled with that
    element. If C{threadgen} is a function, then it is evaluated, and is expected to yield an
    integer or sequence, which is then handled as already described. If C{threadgen} is
    a cluster specification, then the command is executed on each specified host; the thread label
    identifies the host, (whose type is C{osh.cluster.Host}). If C{merge_key} is specified, then
    the inputs of each thread are expected to be ordered by the C{merge_key}. The sequences
    from the threads
    are then merged into a single sequence using the C{merge_key}.
    """
    import osh.apiparser
    op = _Fork()
    if isinstance(command, osh.core.Op):
        command = [command]
    pipeline = osh.apiparser._sequence_op(command)
    if merge_key:
        return op.process_args(threadgen, pipeline, merge_key)
    else:
        return op.process_args(threadgen, pipeline)

class _Fork(osh.core.Generator):

    # state

    _threads = None
    _pipeline = None
    _merge_key = None
    _function_store = None
    _cluster_required = None

    # object interface
    
    def __init__(self):
        osh.core.Generator.__init__(self, '', (2, 3))
        self._function_store = FunctionStore()
        self._cluster_required = False


    # BaseOp interface
    
    def doc(self):
        return __doc__

    def setup(self):
        args = self.args()
        threadgen = args.next()
        self._pipeline = args.next()
        self._merge_key = args.next()
        cluster, thread_ids = self.thread_ids(threadgen)
        self.setup_pipeline(cluster)
        self.setup_threads(thread_ids)
        self.setup_shared_state()

    def receive_complete(self):
        for thread in self._threads:
            thread.pipeline.receive_complete()


    # generator interface

    def execute(self):
        for thread in self._threads:
            thread.pipeline.setup()
            thread.pipeline.set_receiver(self._receiver)
            thread.start()
        for thread in self._threads:
            while thread.isAlive():
                thread.join(0.1)
            thread_termination = thread.terminating_exception
            if thread_termination:
                osh.error.exception_handler(thread_termination, self, None, thread)

    # For use by this package

    def _set_cluster_required(self, required):
        self._cluster_required = required

    # For use by this class

    def thread_ids(self, threadgen, already_evaled = False):
        threadgen_type = type(threadgen)
        try:
            cluster = None
            thread_ids = None
            if threadgen_type in (list, tuple):
                thread_ids = threadgen
            elif isinstance(threadgen, int):
                thread_ids = range(threadgen)
            elif threadgen.isdigit():
                thread_ids = range(int(threadgen))
            elif threadgen_type is types.FunctionType:
                if already_evaled:
                    self.usage()
                else:
                    cluster, thread_ids = self.thread_ids(create_function(threadgen)(), True)
            else:
                # String, which might be a CLI function invocation
                cluster_name, pattern = (threadgen.split(':') + [None])[:2]
                cluster = osh.cluster.cluster_named(cluster_name, pattern)
                if cluster:
                    thread_ids = cluster.hosts
                else:
                    evaled_threadgen = create_function(threadgen)()
                    cluster, thread_ids = self.thread_ids(evaled_threadgen, True)
            if self._cluster_required and cluster is None:
                # API invoked remote but did not identify a cluster
                import remote
                self.usage(remote.__doc__)
            if thread_ids is None:
                self.usage()
            return cluster, thread_ids
        except:
            self.usage()

    def setup_pipeline(self, cluster):
        if cluster and not self._pipeline.run_local():
            remote_op = _Remote()
            remote_op.process_args(self._pipeline)
            self._pipeline = osh.core.Pipeline()
            self._pipeline.append_op(remote_op)
        self._pipeline.append_op(_AttachThreadState())
        self._pipeline.append_op(merge.merge(self._merge_key))

    def setup_threads(self, thread_ids):
        pipeline_copier = _PipelineCopier(self)
        # Use FunctionStore to hide functions during pipeline copying
        self._function_store.hide_functions(self._pipeline)
        threads = []
        for thread_id in thread_ids:
            pipeline_copy = pipeline_copier.pipeline(thread_id)
            thread = osh.oshthread._OshThread(self, thread_id, pipeline_copy)
            threads.append(thread)
        self._function_store.restore_functions(self._pipeline)
        self._threads = threads

    def setup_shared_state(self):
        # Set up shared state for each command in the pipeline: Traverse the pipelines
        # in parallel. Use self._pipeline to allocate the shared state, and then pass the
        # state to each copy.
        pipeline_copy_iterators = [thread.pipeline.ops() for thread in self._threads]
        for pipeline_template_op in self._pipeline.ops():
            command_state = pipeline_template_op.create_command_state(self._threads)
            for pipeline_copy_iterator in pipeline_copy_iterators:
                pipeline_copy_op = pipeline_copy_iterator.next()
                pipeline_copy_op.set_command_state(command_state)
                        
class _PipelineCopier(object):

    _fork = None
    
    def __init__(self, fork):
        self._fork = fork

    def pipeline(self, thread_state):
        copy = osh.util.clone(self._fork._pipeline)
        self._fork._function_store.restore_functions(copy)
        return copy

class _AttachThreadState(osh.core.Op):

    _thread_state = None

    def __init__(self):
        osh.core.Op.__init__(self, '', (0, 0))

    def setup(self):
        self._thread_state = (self.thread_state,)

    def receive(self, object):
        if type(object) is list:
            object = tuple(object)
        self.send(self._thread_state + object)

# osh needs to copy pipelines to support forks. 
# 1. Pickling: doesn't handle functions.
# 2. Marshaling: doesn't handle recursive structures. Pipelines are recursive due to BaseOp.parent.
# 3. Add a clone method to the BaseOp interface. Lots of work to handle recursion.
# This implementation is a combination of 1 and 3: BaseOp.replace_function_by_reference
# replaces functions by integer references to functions. BaseOp.restore_function does the
# inverse. A pipeline is copied by:
# - Apply replace_function_by_reference recursively to the input pipeline.
# - Copy the pipeline.
# - Apply restore_function to the copy.

class FunctionReference(int):
    pass
    
class FunctionStore(object):

    _functions = None
    
    def __init__(self):
        self._functions = []

    # For use by this module
        
    def hide_functions(self, pipeline):
        pipeline.replace_function_by_reference(self)

    def restore_functions(self, pipeline):
        pipeline.restore_function(self)

    # For use by BaseOp subclasses in hiding and restoring functions
        
    def function_to_reference(self, x):
        if type(x) is types.FunctionType:
            position = FunctionReference(len(self._functions))
            self._functions.append(x)
            return position
        else:
            return x

    def reference_to_function(self, x):
        if type(x) is FunctionReference:
            return self._functions[x]
        else:
            return x

# Remote execution
        
_REMOTE_EXECUTABLE = 'remoteosh'

def _dump(stream, object):
    stream.dump(object)

def _consume_remote_stdout(consumer, threadid, object):
    if isinstance(object, osh.error.PickleableException):
        exception = object.recreate_exception()
        osh.error.exception_handler(exception, object.command_description(), object.input(), threadid)
    else:
        consumer.send(object)

def _consume_remote_stderr(consumer, threadid, line):
    # UGLY HACK: remoteosh can occasionally return "[Errno 9] Bad file descriptor" on stderr.
    # I think this is because of io to a process stream whose process has completed.
    # I haven't had luck in tracking this down and fixing the problem for real, so
    # this is a grotesque workaround.
    if '[Errno 9] Bad file descriptor' not in line:
        osh.error.stderr_handler(line, consumer, None, threadid)

class _Remote(osh.core.Generator):

    # state

    _pipeline = None

    # object interface
    
    def __init__(self):
        osh.core.Generator.__init__(self, '', (1, 1))

    # BaseOp interface
    
    def doc(self):
        return __doc__

    def setup(self):
        self._pipeline = self.args().next()

    # generator interface

    def execute(self):
        host = self.thread_state
        process = Spawn(
            self._remote_command(host.address, host.user, host.identity, host.db_profile),
            ObjectInputProvider(lambda stream, object: _dump(stream, object),
                                [osh.core.verbosity, self._pipeline, self.thread_state]),
            ObjectOutputConsumer(lambda object: _consume_remote_stdout(self, host, object)),
            LineOutputConsumer(lambda line: _consume_remote_stderr(self, host, line)))
        process.run()
        if process.terminating_exception():
            raise process.terminating_exception()

    # for use by this class

    def _remote_command(self, host, user, identity, db_profile):
        buffer = [_REMOTE_EXECUTABLE]
        if db_profile:
            buffer.append(db_profile)
        remote_command = ' '.join(buffer)
        if identity:
            ssh_command = 'ssh %s -l %s -i %s %s' % (host,
                                                     user,
                                                     identity,
                                                     remote_command)
        else:
            ssh_command = 'ssh %s -l %s %s' % (host,
                                               user,
                                               remote_command)
        return ssh_command

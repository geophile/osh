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

"""Objects comprising an osh command's parse tree. Also
includes some classes used at command runtime.
"""

import getopt
import new
import os
import sys
import threading
import types
import traceback
import signal

from config import config_value, config_subset, oshrc_symbols
import cluster
import error
import args
import util

USAGE_API = 'api'
USAGE_CLI = 'cli'
# Assume API. If parser is used then usage will be changed.
osh_usage = USAGE_API

# scp options supported by copyfrom and copyto
SCP_OPTIONS = 'rpC'

# 2.2 threads sometimes hang without this. The 2.2 default is 10, 2.3: 100
sys.setcheckinterval(100)

verbosity = None
default_db_profile = None

def wrap_if_necessary(object):
    if not(isinstance(object, tuple) or isinstance(object, list)):
        object = (object,)
    return object

#--------------------------------------------------------------------------------

class BaseOp(object):
    """Base class for all osh commands, and for pipelines, (sequences of
    commands). Methods of this class implement the command execution and
    inter-command communication. The send* commands are used by subclasses to
    send output to downstream commands. The receive* commands are implemented
    by subclasses to receive and process input from upstream commands.
    """

    # state

    _parent = None
    _next_op = None
    _receiver = None
    _command_state = None


    # object interface
    
    def __repr__(self):
        assert False

    # BaseOp runtime interface

    def usage(self, message = None):
        """Print usage message and exit.
        """
        if message is None:
            message = self.doc()
        sys.stderr.write(message)
        sys.stderr.write('\n')
        sys.exit(-1)

    def doc(self):
        """Print command usage information.
        """
        assert False

    def replace_function_by_reference(self, function_store):
        assert False

    def restore_function(self, function_store):
        assert False
        
    def create_command_state(self, oshthreads):
        return None

    def set_command_state(self, command_state):
        self._command_state = command_state

    def command_state(self):
        return self._command_state

    def setup(self):
        """Setup is executed just prior to command execution. Will be called with self.thread_state
        = None before any forking, providing a chance to set up state shared by threads of a fork.
        """
        assert False

    def execute(self):
        """Execute the command.
        """
        assert False

    def send(self, object):
        """Called by a command class to send an object of command output to
        the next command.
        """
        try:
            if self._receiver:
                self._receiver.receive(wrap_if_necessary(object))
        except error.OshKiller:
            raise
        except Exception, e:
            error.exception_handler(e, self._receiver, object)

    def send_complete(self):
        """Called by a command class to indicate that there will
        be no more output from the command.
        """
        try:
            if self._receiver:
                self._receiver.receive_complete()
        except error.OshKiller:
            raise
        except Exception, e:
            error.exception_handler(e, self._receiver, object)

    def receive(self, object):
        """Implemented by a command class to process an input object.
        """
        pass

    def receive_complete(self):
        """Implemented by a command class to do any cleanup required
        after all input has been received.
        """
        self.send_complete()

    def run_local(self):
        return False

    # BaseOp compile-time interface
    
    def connect(self, new_op):
        last_op  = self
        while last_op._next_op:
            last_op = last_op._next_op
        last_op._next_op = new_op
        return self


    # For use by this package

    def parent(self):
        return self._parent

    def set_parent(self, parent):
        self._parent = parent


#--------------------------------------------------------------------------------

class Op(BaseOp):
    """Base class for all osh commands, (excluding pipelines).
    """

    # state
    
    _args = None


    # object interface
    
    def __init__(self, flag_spec, anon_range):
        BaseOp.__init__(self)
        if osh_usage == USAGE_API:
            self._args = args.ArgsAPI(self, flag_spec, anon_range)
        elif osh_usage == USAGE_CLI:
            self._args = args.ArgsCLI(self, flag_spec, anon_range)
        else:
            assert False

    def __repr__(self):
        return '%s<%s>%s' % (self._command_name(), id(self), self._args)


    # BaseOp interface

    def replace_function_by_reference(self, function_store):
        self._args.replace_function_by_reference(function_store)

    def restore_function(self, function_store):
        self._args.restore_function(function_store)
        
    def execute(self):
        assert False

    # def receive_complete(self):
    #     self.send_complete()


    # Op compile-time interface
    
    def add_arg(self, arg):
        arg_description = str(arg)
        self._args.add_token(arg)
        return self

    def args_done(self):
        try:
            self._args.args_done()
        except args.ArgException, e:
            print >>sys.stderr, e
            sys.exit(1)
        return self

        
    # Op interface - for use by subclasses

    def process_args(self, *args):
        for arg in args:
            self._args.add_arg(arg)
        self._args.args_done()
        return self

    def args(self):
        return self._args

    thread_state = property(lambda self: self._parent._thread_state)


    
    # for use by this class

    def _command_name(self):
        classname = str(self.__class__)
        # classname is <class 'MODULE.CLASSNAME'>. First get rid of everything bug MODULE.CLASSNAME.
        first_quote = classname.find("'")
        assert first_quote > 0, classname
        second_quote = classname.find("'", first_quote + 1)
        assert second_quote > 0, classname
        classname = classname[first_quote + 1 : second_quote]
        # Convert _Foo to foo
        classname = classname.split('.')[-1]
        assert len(classname) >= 2, classname
        assert classname[0] == '_', classname
        assert classname[1].isupper(), classname
        return classname[1:].lower()

#--------------------------------------------------------------------------------

class Pipeline(BaseOp):

    # state

    _first_op = None
    _thread_state = None
    

    # object interface

    def __init__(self, op = None):
        BaseOp.__init__(self)
        if op:
            self.append_op(op)

    def __repr__(self):
        buffer = []
        op = self._first_op
        while op:
            buffer.append(str(op))
            op = op._next_op
        return 'pipeline<%s>(%s)' % (id(self), ' ^ '.join(buffer))


    # BaseOp interface

    def replace_function_by_reference(self, function_store):
        op = self._first_op
        while op:
            op.replace_function_by_reference(function_store)
            op = op._next_op

    def restore_function(self, function_store):
        op = self._first_op
        while op:
            op.restore_function(function_store)
            op = op._next_op

    def setup(self):
        op = self._first_op
        while op:
            op.setup()
            next = op._next_op
            if next:
                op._receiver = next
            else:
                op._receiver = self._pipeline_receiver()
            op = next

    def execute(self):
        try:
            self._first_op.execute()
        except error.OshKiller:
            raise
        except Exception, e:
            error.exception_handler(e, self._first_op, None)

    def receive(self, object):
        self._first_op.receive(object)

    def receive_complete(self):
        self._first_op.receive_complete()

    def run_local(self):
        run_local = True
        op = self._first_op
        while run_local and op:
            run_local = op.run_local()
            op = op._next_op
        return run_local

    # Pipeline runtime interface

    def set_thread_state(self, thread_state):
        self._thread_state = thread_state

    def ops(self):
        op = self._first_op
        while op:
            yield op
            op = op._next_op

    # For use in setting up output for forks. Set this pipeline's receiver to op's receiver
    def set_receiver(self, op):
        pipeline_op = self._first_op
        while pipeline_op._next_op:
            pipeline_op = pipeline_op._next_op
        pipeline_op._receiver = op

    # Pipeline compile-time interface

    def append_op(self, op):
        if self._first_op:
            self._first_op.connect(op)
        else:
            self._first_op = op
        op.set_parent(self)
        return self

    def prepend_op(self, op):
        if self._first_op:
            self._first_op = op.connect(self._first_op)
        else:
            self._first_op = op
        op.set_parent(self)
        return self


    # For use by this class

    def _pipeline_receiver(self):
        receiver = self._next_op
        if not receiver:
            parent = self._parent
            if parent:
                receiver = parent._pipeline_receiver()
            else:
                receiver = None
        return receiver


 #--------------------------------------------------------------------------------

class Generator(Op):
    """Base class of osh commands that are generators, e.g. gen, timer.
    """

    # object interface

    def __init__(self, flag_spec, anon_range):
        Op.__init__(self, flag_spec, anon_range)


    # BaseOp interface

    def generator(self):
        return True

    # Allows one generator to be run under the control of another
    # (e.g. timer)
    def receive(self, object):
        self.execute()


    # Generator interface

    def execute(self):
        assert False, self

#--------------------------------------------------------------------------------

class RunLocal(Generator):

    def __init__(self, flag_spec, anon_range):
        Generator.__init__(self, flag_spec, anon_range)

    def run_local(self):
        return True
        
#--------------------------------------------------------------------------------

def _ctrl_c_handler(signal, frame):
    # Set error and exception handlers to be quiet.
    import error
    error.set_stderr_handler(lambda line, op, input, thread: None)
    error.set_exception_handler(lambda exception, op, input, thread: None)
    # kill spawned processes (including remote)
    spawn.kill_all_processes()
    
class Command(object):
    _pipeline = None

    def __init__(self, pipeline):
        self._pipeline = pipeline

    def __repr__(self):
        return str(self._pipeline)

    def execute(self):
        original_ctrl_c_handler = signal.signal(signal.SIGINT, _ctrl_c_handler)
        try:
            try:
                # Prepare for execution
                self._pipeline.setup()
                if verbosity >= 1:
                    print str(self._pipeline)
                # Execute
                self._pipeline.execute()
                self._pipeline.receive_complete()
            except error.OshKiller, e:
                print >>sys.stderr, e.cause
            except Exception, e:
                print >>sys.stderr, e
        finally:
            if original_ctrl_c_handler is not None:
                signal.signal(signal.SIGINT, original_ctrl_c_handler)

    def pipeline(self):
        return self._pipeline

#--------------------------------------------------------------------------------

#
# Namespace of osh command
#

_namespace = oshrc_symbols.copy()
        
def add_to_namespace(key, value):
    _namespace[key] = value

def namespace():
    return _namespace

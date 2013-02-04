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

"""The osh API (Application Programming Interface) supports the use of osh from Python code.
The recommended form of import is C{from osh.api import *}. This imports
the functions documented here as well as
the symbols from the module C{osh.builtins},
the C{Process} class, and C{processes}
function.

In general, the function C{F()} can be found in the module
C{osh.command.F}. See documentation for the package osh.command for
information on each function.
"""

import sys
import types

from args import Option
import apiparser
import core
import config
import error
import command
import command.f
from builtins import *

# Get symbols defined in .oshrc
globals().update(core.namespace())

def _import_package(package_name):
    package = globals()[package_name]
    for module_name in package.__all__:
        exec('import %s.%s' % (package_name, module_name))
        mod = getattr(package, module_name)
        for element_name in dir(mod):
            if not element_name.startswith('_'):
                element = getattr(mod, element_name)
                if type(element) is types.FunctionType:
                    globals()[element_name] = element

def create_commands(package_name, command_names):
    commands = {}
    for command_name in command_names:
        command_module = __import__('%s.%s' % (package_name, command_name), globals(), locals(), command_name)
        commands[command_name] = getattr(command_module, command_name)
    return commands

# Top-level api invocation

def osh(*ops):
    """Invoke osh interpreter. Each argument is a function invocation identifying a command.
    The command sequence corresponds to the sequence of arguments.
    """
    # Construct the pipeline
    pipeline = None
    try:
        pipeline = apiparser._sequence_op(ops)
    except Exception, e:
        print >>sys.stderr, e
        sys.exit(1)
    # Run
    command = core.Command(pipeline)
    command.execute()
    last_op = ops[-1]
    if type(last_op) is _ReturnList:
        return last_op.list
    else:
        return None

class _ReturnList(core.Op):

    _unwrap_singleton = None
    _list = None

    def __init__(self, unwrap_singleton):
        core.Op.__init__(self, '', (0, 0))
        self._unwrap_singleton = unwrap_singleton
        self._list = []

    def setup(self):
        pass

    def receive(self, object):
        if self._unwrap_singleton and len(object) == 1:
            self._list.append(object[0])
        else:
            self._list.append(object)

    def receive_complete(self):
        self.send_complete()

    list = property(lambda self: self._list)
        

def return_list(unwrap_singleton = True):
    """Input tuples are accumulated in a list which is returned as the value of the
    C{osh()} invocation. If unwrap_singleton is True, then items in the list that
    are 1-object sequences are unwrapped, e.g. (419,) -> 419.
    """
    return _ReturnList(unwrap_singleton)


# Error and exception handling

def set_error_handler(handler):
    """Replaces the standard error handler (which prints to stderr). An error handler
    takes these arguments:
        - C{line}: A line printed to stderr by the failing operation.
        - C{op}: The failing operation.
        - C{input}: The input to the failing operation.
        - C{host}: The host on which the error occurred (in case of remote execution).
    """
    error.set_error_handler(handler)

def set_exception_handler(handler):
    """Replaces the standard exception handler (which prints to stderr). An exception handler
    takes these arguments:
        - C{exception}: The exception being handled.
        - C{op}: The operation that caused the exception.
        - C{input}: The input to the operation that caused the exception.
        - C{host}: The host on which the exception occurred (in case of remote execution).
    """
    error.set_exception_handler(handler)

    
# Debugging

def debug(verbosity):
    """Control osh debugging: 0 = off, 1 = parse tree, 2 = command execution.
    """
    core.verbosity = verbosity


# Setup

_import_package('command')

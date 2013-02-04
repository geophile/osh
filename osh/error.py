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

"""Controls handling of exceptions and stderr through the setting of handlers.

An C{exception_handler} is a function with these arguments:
    - C{exception}: The exception being handled. In case of a remote exception, this exception object is a client-side reconstruction of the server-side exception.
    - C{op}: A command of type C{Op}, or, in case of a remote exception, a command description, obtained by applying C{str()}.
    - C{input}: Input to the command that raised the exception.
    - C{thread}: The thread on which the exception occurred.

An C{error_handler} is a function with these arguments:
    - C{line}: A line written to stderr.
    - C{op}: A command of type C{Op}, or, in case of remote stderr output, a command description, obtained by applying C{str()}.
    - C{input}: Input to the command that generated the stderr output.
    - C{thread}: The thread on which the stderr output occurred,
"""

import sys
import new

import util

class PickleableException(object):

    _command_description = None
    _input = None
    _exception_args = None
    _exception_type_name = None
    _exception_message = None

    def __init__(self, command_description, input, exception):
        self._command_description = command_description
        self._input = input
        self._exception_args = exception.args
        self._exception_type_name = str(exception.__class__)
        self._exception_message = str(exception)

    def __str__(self):
        return ('Encountered %s during execution of %s on input %s: %s' %
                (self._exception_type_name,
                 self._command_description,
                 self._input,
                 self._exception_message))

    def recreate_exception(self):
        last_dot = self._exception_type_name.rfind('.')
        assert last_dot > 0, self._exception_type_name
        module_name = self._exception_type_name[:last_dot]
        exec 'import %s' % module_name
        klass = eval(self._exception_type_name)
        return eval('%s(%s)' % (self._exception_type_name, util.quote(str(self))))

    def command_description(self):
        return self._command_description

    def input(self):
        return self._input

#----------------------------------------------------------------------

# Exception and error handling

# Exception thrown by exception handler needs to terminate osh.
# Use OshKiller to tunnel through except blocks.

class OshKiller(Exception):

    def __init__(self, cause):
        Exception.__init__(self)
        self.cause = cause

    def __str__(self):
        return str(self.cause)


# exception_handler is a function with these arguments:
# - exception: The exception being handled. In case of a remote exception, this exception
#   object is a client-side reconstruction of the server-side exception.
# - op: A command of type Op, or, in case of a remote exception, a command description,
#   obtained by applying str().
# - thread: The thread on which the exception occurred, or None if it occurred locally.

exception_handler = None
stderr_handler = None
    
def _format_input_for_reporting(input, buffer):
    if isinstance(input, list):
        buffer.append(str(tuple(input)))
    elif isinstance(input, tuple):
        buffer.append(str(input))
    else:
        buffer.append('(')
        buffer.append(str(input))
        buffer.append(')')

def _default_exception_handler(exception, op, input, thread = None):
    buffer = []
    if thread:
        buffer.append('on ')
        buffer.append(str(thread))
        buffer.append(': ')
    buffer.append(str(op))
    _format_input_for_reporting(input, buffer)
    buffer.append(' ')
    buffer.append(str(exception.__class__))
    buffer.append(': ')
    buffer.append(str(exception))
    print >>sys.stderr, ''.join(buffer)

def set_exception_handler(handler):
    """Use C{handler} as the exception handler.
    """
    global exception_handler
    def wrap_provided_exception_handler(exception, op, input, thread = None):
        try:
            handler(exception, op, input, thread)
        except Exception, e:
            raise OshKiller(e)
    exception_handler = wrap_provided_exception_handler

exception_handler = _default_exception_handler

def _default_stderr_handler(line, op, input, thread = None):
    buffer = []
    if thread:
        buffer.append('on ')
        buffer.append(str(thread))
        buffer.append(': ')
    buffer.append(str(op))
    _format_input_for_reporting(input, buffer)
    buffer.append(': ')
    buffer.append(line.rstrip())
    print >>sys.stderr, ''.join(buffer)

def set_stderr_handler(handler):
    """Use C{handler} as the stderr handler.
    """
    def wrap_provided_stderr_handler(line, op, input, thread = None):
        try:
            handler(line, op, input, thread)
        except Exception, e:
            raise OshKiller(e)
    global stderr_handler
    stderr_handler = wrap_provided_stderr_handler

stderr_handler = _default_stderr_handler

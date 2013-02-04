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

"""Encapsulates functions used in osh commands such as C{f} and C{select}.

osh function syntax::

    [[lambda] ARGS:] EXPRESSION

C{ARGS}: Comma-separated list of function arguments, optionally preceded by keyword
C{lambda}. C{ARGS} may be omitted only for a function with no arguments.

C{EXPRESSION}: A Python expression written in terms of the function arguments.

Example::

    x: max(x, 10)
"""

import copy
import sys
import types

import core

_LAMBDA = 'lambda '
_LAMBDA_COLON = 'lambda:'

# "Private" name (with leading underscore) so that epydoc doesn't document the class
class _Function(object):
    """Represents a function for use by osh commands with function arguments,
    e.g., select.
    """
    
    _function_spec = None
    _function = None
    _function_id = None

    def __init__(self, function_spec, namespace = core.__dict__):
        """Creates a Function.
        - function_spec: String specification of a function. Uses lambda notation,
          but the 'lambda' keyword is optional.
        - namespace: The default is reasonable; there's been no need to
          override it so far.
        """
        if type(function_spec) in (types.FunctionType, types.BuiltinFunctionType):
            self._function = function_spec
        else:
            self._function_spec = function_spec
            lambda_expression = self.parse(function_spec.strip())
            # Create a namespace including symbols defined by the current osh invocation.
            namespace = copy.copy(namespace)
            namespace.update(core.namespace())
            self._function = eval(lambda_expression, namespace)

    def __repr__(self):
        return 'function(%s)' % self._function_spec
            
    def __call__(self, *args): # args = None):
        return self._function(*args)

    def parse(self, function_spec):
        # If the function spec starts with a lambda, then just use it as is.
        # Otherwise, it could be:
        # - function with arg list, e.g. "x, y: x + y"
        # - zero-arg list with colon, e.g. ": processes()"
        # - zero-arg list without colon, e.g. "processes()"
        # Try prepending "lambda:" and "lambda" until there's
        # no syntax error. Crude but effective.
        if function_spec.startswith(_LAMBDA) or function_spec.startswith(_LAMBDA_COLON):
            # ok as is
            pass
        else:
            fixed_function_spec = '%s: %s' % (_LAMBDA, function_spec)
            try:
                eval(fixed_function_spec)
                function_spec = fixed_function_spec
            except:
                fixed_function_spec = '%s %s' % (_LAMBDA, function_spec)
                try:
                    eval(fixed_function_spec)
                    function_spec = fixed_function_spec
                except:
                    raise NotAFunctionException('Illegal function spec: %s' % function_spec)
        return function_spec

class NotAFunctionException(Exception):

    def __init__(self, message):
        Exception.__init__(self, message)

def _operator_to_function(op):
    if op == '+':
        f = lambda x, y: x + y
    elif op == '*':
        f = lambda x, y: x * y
    elif op == '^':
        f = lambda x, y: x ^ y
    elif op == '&':
        f = lambda x, y: x & y
    elif op == '|':
        f = lambda x, y: x | y
    elif op == 'and':
        f = lambda x, y: x and y
    elif op == 'or':
        f = lambda x, y: x or y
    elif op == 'max':
        f = lambda x, y: max(x, y)
    elif op == 'min':
        f = lambda x, y: min(x, y)
    else:
        f = None
    return f

def _create_function(x):
    f = None
    if type(x) in [types.FunctionType, types.BuiltinFunctionType]:
        f = _Function(x)
    elif isinstance(x, str):
        op = _operator_to_function(x)
        if op:
            f = _Function(op)
        else:
            f = _Function(x)
    return f

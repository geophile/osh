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

_STATE_ANONYMOUS = 'anonymous'
_STATE_BEFORE_KEY = 'before_key'
_STATE_BETWEEN_KEY_AND_VAL = 'between_key_and_val'

_KEY_AND_VALUE = True
_KEY_ONLY = False

def _function(x):
    import function
    f = function._create_function(x)
    if f is None:
        raise ValueError('%s is not a function' % x)
    return f

class Option(object):

    _key = None
    _val = None

    def __init__(self, key, val = True):
        self._key = key
        self._val = val

    def __repr__(self):
        return 'option(%s: %s)' % (str(self._key), str(self._val))

    def key(self):
        return self._key

    def value(self):
        return self._val

class Args(object):

    _op = None
    _valid_keys = None # map: key -> _KEY_AND_VALUE/_KEY_ONLY
    _min_anon = None
    _max_anon = None
    _keyval = None
    _anon = None # list, args removed on each call to a next_ method.
    _anon_counter = 0

    def __init__(self, op, flag_spec, anon_range):
        self._valid_keys = {}
        last_key = None
        last_char = None
        if flag_spec:
            for c in flag_spec:
                if c == ':':
                    if last_key is None or last_char == ':':
                        raise ArgException('Illegal flag specification for %s: %s' %
                                              (self._op, flag_spec))
                    self._valid_keys['-' + last_key] = True
                else:
                    self._valid_keys['-' + c] = False
                    last_key = c
                last_char = c
        self._op = op
        self._min_anon, self._max_anon = anon_range
        self._keyval = {}
        self._anon = []

    def __repr__(self):
        repr = []
        if len(self._keyval) > 0:
            repr.append('{')
            first = True
            for key, val in self._keyval.iteritems():
                if first:
                    first = False
                else:
                    repr.append(', ')
                repr.append(str(key))
                if val != True:
                    repr.append(': ')
                    repr.append(str(val))
            repr.append('}')
        repr.append('[')
        first = True
        for arg in self._anon:
            if first:
                first = False
            else:
                repr.append(', ')
            repr.append(str(arg))
        repr.append(']')
        return ''.join(repr)

    def add_arg(self, arg):
        # Expand -xyz to -x -y -z
        if isinstance(arg, Option):
            key = arg.key()
            if key[0] == '-':
                key = key[1:]
            for flag in key:
                flag = '-' + flag
                flag_type = self._valid_keys.get(flag, None)
                if flag_type is None:
                    raise ArgException('%s is not a valid key for %s' % (flag, self._op))
                elif flag_type == _KEY_AND_VALUE and isinstance(arg.value(), bool):
                    raise ArgException('No value specified for %s' % flag)
                elif flag_type == _KEY_ONLY and not isinstance(arg.value(), bool):
                    raise ArgException('Should not specify a value for %s' % flag)
                if flag in self._keyval:
                    raise ArgException('Attempt to specify multiple values for %s' % flag)
                self._keyval[flag] = arg.value()
        else:
            self._anon.append(arg)

    def args_done(self):
        if len(self._anon) < self._min_anon:
            raise ArgException('Too few arguments for %s' % self._op)
        if self._max_anon is not None and len(self._anon) > self._max_anon:
            raise ArgException('Too many arguments for %s' % self._op)

    def int_arg(self, key):
        val = self._keyval.get(key, None)
        if val is not None:
            val = int(val)
        return val

    def string_arg(self, key):
        val = self._keyval.get(key, None)
        if val is not None:
            val = str(val)
        return val

    def function_arg(self, key):
        val = self._keyval.get(key, None)
        if val is not None:
            val = _function(val)
        return val

    def arg(self, key):
        return self._keyval.get(key, None)

    # CLI: evaluate it
    # API: return as is
    def eval_arg(self, key):
        assert False

    def flag(self, key):
        return self._keyval.get(key, None)

    def has_next(self):
        return self._anon_counter < len(self._anon)

    def next_int(self):
        if self.has_next():
            arg = self._next_anon()
            if arg is None:
                val = None
            else:
                val = int(arg)
        else:
            val = None
        return val

    def next_string(self):
        if self.has_next():
            arg = self._next_anon()
            if arg is None:
                val = None
            else:
                val = str(arg)
        else:
            val = None
        return val

    def next_function(self):
        if self.has_next():
            arg = self._next_anon()
            if arg is None:
                val = None
            else:
                val = _function(arg)
        else:
            val = None
        return val

    def next(self):
        return self._next_anon()

    # CLI: evaluate it
    # API: return as is
    def next_eval(self):
        assert False

    def remaining(self):
        remaining = self._anon[self._anon_counter:]
        self._anon_counter = len(self._anon)
        return remaining

    # For use by this package

    def replace_function_by_reference(self, function_store):
        for key, val in self._keyval.iteritems():
            replacement = function_store.function_to_reference(val)
            if replacement is not val:
                self._keyval[key] = replacement
        self._anon = [function_store.function_to_reference(arg) for arg in self._anon]

    def restore_function(self, function_store):
        for key, val in self._keyval.iteritems():
            replacement = function_store.reference_to_function(val)
            if replacement is not val:
                self._keyval[key] = replacement
        self._anon = [function_store.reference_to_function(arg) for arg in self._anon]

    # For use by this module

    def _next_anon(self):
        if self.has_next():
            a = self._anon[self._anon_counter]
            self._anon_counter += 1
        else:
            a = None
        return a

    def _flag_type(self, flag):
        return self._valid_keys.get(flag, None)

class ArgsAPI(Args):

    def __init__(self, op, flag_spec, anon_range):
        Args.__init__(self, op, flag_spec, anon_range)

    def eval_arg(self, key):
        return self._keyval[key]

    def next_eval(self):
        if self.has_next():
            val = self._next_anon()
        else:
            val = None
        return val


class ArgsCLI(Args):

    _tokens = None

    def __init__(self, op, flag_spec, anon_range):
        Args.__init__(self, op, flag_spec, anon_range)
        self._tokens = []

    def add_token(self, token):
        self._tokens.append(token)

    def eval_arg(self, key):
        return eval(self._keyval[key])

    def next_eval(self):
        if self.has_next():
            val = eval(self._next_anon())
        else:
            val = None
        return val

    def args_done(self):
        if self._tokens is not None:
            state = _STATE_BEFORE_KEY
            prev_token = None
            for token in self._tokens:
                state = self._process_a_token(state, prev_token, token)
                prev_token = token
            self._tokens = None
        Args.args_done(self)

    def _process_a_token(self, state, prev_token, token):
        if state is _STATE_BEFORE_KEY:
            if self._flag(token):
                state = self._initialize_key_token(token)
            else:
                self._anon.append(token)
                state = _STATE_ANONYMOUS
        elif state is _STATE_BETWEEN_KEY_AND_VAL:
            if self._flag(token):
                self._initialize_key_token(token)
            else:
                if len(prev_token) > 2:
                    # -xyz val: Treat x, y, z as flags, and val as anon.
                    self._initialize_key_token(prev_token)
                    self._anon.append(token)
                    state = _STATE_ANONYMOUS
                else:
                    self._keyval[prev_token] = token
                    state = _STATE_BEFORE_KEY
        elif state is _STATE_ANONYMOUS:
            self._anon.append(token)
        else:
            assert False
        return state

    def _flag(self, arg):
        if isinstance(arg, str) and arg.startswith('-'):
            try:
                int(arg)
                # Must be a negative number or a flag
                if self._valid_keys.get(arg, None) is False:
                    return True
                else:
                    return False
            except ValueError:
                return True
        else:
            return False

    # Turn -xyz into -x -y -z. (Makes sense only for flags -- no val).
    # For a key/val, this does the right thing; val will come along as the
    # next token.
    def _initialize_key_token(self, token):
        multiflag = len(token) > 2
        for x in token[1:]:
            flag = '-' + x
            flag_type = self._flag_type(flag)
            if flag_type is None:
                raise ArgException('Undefined flag for %s: %s' % (self._op, flag))
            # -xyz means that x, y and z must be _KEY_ONLY
            if flag_type == _KEY_AND_VALUE and multiflag:
                raise ArgException("%s needs a value so don't include it with others: %s" %
                                      (flag, token))
            self._keyval[flag] = True
        next_state = _STATE_BEFORE_KEY
        if not multiflag and flag_type == _KEY_AND_VALUE:
            next_state = _STATE_BETWEEN_KEY_AND_VAL
        return next_state

class ArgException(Exception):

    def __init__(self, message):
        Exception.__init__(self, message)

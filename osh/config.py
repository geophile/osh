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

import os
import sys
import traceback
import types

from error import *
import spawn

# osh configuration

_configuration = {}

class Config(object):
    """key/value pairs used to configure osh. key is a string of
    dot-separated tokens with these properties:
    - First token is 'osh'.
    - All tokens are legal python identifiers.
    The value may be any python object.
    """
    
    _tokens = None

    def __init__(self):
        # Can't assign to self._tokens because __setattr__ would be invoked.
        object.__setattr__(self, '_tokens', [])

    def __getattr__(self, token):
        self._tokens.append(token)
        return self

    def __setattr__(self, token, value):
        self._tokens.append(token)
        _configuration[self.key()] = value

    def __getitem__(self, key):
        self._tokens.append(key)
        return self

    def __setitem__(self, key, value):
        self._tokens.append(key)
        _configuration[self.key()] = value

    def key(self):
        return '.'.join(self._tokens)

class _ConfigFactory(object):

    def __getattr__(self, token):
        return Config().__getattr__(token)

    def __setattr__(self, token, value):
        return Config().__setattr__(token, value)

    def __getitem__(self, key):
        return Config().__getitem__(key)

    def __setitem__(self, key, value):
        return Config().__setattr__(key, value)

osh = _ConfigFactory()

def _default_profile(command):
    """The default profile name for an osh command. E.g., if osh.remote='foobar',
    then 'osh @ [ ... ]' is equivalent to 'osh @foobar [...]'.
    """
    return _configuration[command]

def config_value(*args):
    """Returns the configuration value specified by args. E.g., if
    osh.a.b.c='xyz' then config_value('a', 'b', 'c') returns 'xyz'.
    """
    if len(args) == 1:
        configKey = args[0]
    elif len(args) == 3:
        command = args[0]
        profile = args[1]
        key = args[2]
        if profile is None:
            profile = _default_profile(command)
        configKey = '%s.%s.%s' % (command, profile, key)
    else:
        sys.stderr.write('Illegal arguments to config.get: %s' %
                         str(args))
    return _configuration.get(configKey, None)

# returns config key/value pairs, such that key starts with prefix. Prefix is
# omitted in keys of output.
def config_subset(prefix):
    if prefix[-1] != '.':
        prefix = prefix + '.'
    subset = {}
    for key, value in _configuration.iteritems():
        if key.startswith(prefix):
            key_suffix = key[len(prefix):]
            subset[key_suffix] = value
    return subset
    

# Read user's configuration

def findconfig():
    # Check .oshrc in local directory.
    # Then check .oshrc in home directory
    # Finally, check /etc/oshrc
    paths = [ '.oshrc' ]
    if os.getenv('HOME'):
        paths.append(os.getenv('HOME') + '/.oshrc')
    paths.append('/etc/oshrc')
    oshrc_path = None
    for path in paths:
        if os.path.isfile(path):
            oshrc_path = path
            break
    if not oshrc_path:
        oshrc_path = os.getenv('HOME') + '/.oshrc'
        oshrc_file = open(oshrc_path, 'w')
        print >>oshrc_file, 'from osh.config import *\n'
        oshrc_file.close()
    return oshrc_path

# osh environment

OSH_HOME = '/usr/share/osh'
OSH_VERSION = '1.0.3'
OSH_SUBVERSION = ''

# global constants and variables

verbosity = 0

_before = globals().copy()
execfile(findconfig())
_after = globals().copy()
oshrc_symbols = {}
# Populate namespace used by commands with symbols defined in .oshrc.
# Don't use set so that Python 2.3 works.
for key, value in _after.iteritems():
    if key not in _before:
        oshrc_symbols[key] = value

# osh package path (set this after reading config file)

oshpath = config_value('path')
if not oshpath:
    oshpath = []

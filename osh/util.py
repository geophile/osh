#!/usr/bin/python

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
        
import cPickle
import StringIO

import spawn
Spawn = spawn.Spawn
SpawnSSH = spawn.SpawnSSH
collect_lines = spawn.collect_lines

def remove_crlf(line):
    if line.endswith('\r\n'):
        return line[:-2]
    elif line.endswith('\n'):
        return line[:-1]
    else:
        return line

def clone(x):
    buffer = StringIO.StringIO()
    pickler = cPickle.Pickler(buffer)
    pickler.dump(x)
    buffer.seek(0)
    unpickler = cPickle.Unpickler(buffer)
    return unpickler.load()

def scp(user, identity, host, flags, source, target):
    err_lines = []
    if flags is None:
        flags = ''
    if identity:
        scp_command = 'scp %s %s -i %s %s@%s:%s' % (flags,
                                                    source,
                                                    identity,
                                                    user,
                                                    host,
                                                    target)
    else:
        scp_command = 'scp %s %s %s@%s:%s' % (flags,
                                              source,
                                              user,
                                              host,
                                              target)
    Spawn(scp_command,
          None,
          None,
          collect_lines(err_lines)).run()
    if len(err_lines) > 0:
        raise Exception(' '.join(err_lines))

def ssh(user, identity, host, command):
    output = []
    errors = []
    SpawnSSH(user,
             identity,
             host,
             command,
             None,
             collect_lines(output),
             collect_lines(errors)).run()
    return output, errors

def quote(s):
    if '\n' in s:
        return '"""%s"""' % s
    elif "'" not in s:
        return "'%s'" % s
    elif '"' not in s:
        return '"%s"' % s
    else:
        return '"""%s"""' % s

def print_stack():
    import traceback
    traceback.print_stack()
    return None
    # import inspect
    # buffer = []
    # for frame in inspect.stack():
    #     buffer.append('    %s:%s - %s' % (frame[1], frame[2], frame[4][0]))
    # return '\n'.join(buffer)

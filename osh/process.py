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

"""Provides information on currently running processes, by examining files in the C{/proc} filesystem.
(So it doesn't work on OS X, for example.) The C{processes} function returns a list of C{Process}
objects. Each C{Process} object reveals information derived from C{/proc}, identifies
parent and child processes, and can be used to send signals to the process.
"""

import os
import os.path
import pickle

def processes(*dummy):
    """Returns a list of process objects based on the current contents of C{/proc}.
    Of course the list is stale as soon as it is formed. In particular, a C{Process}
    object in the list may correspond to a process that has terminated by the time
    you use the object.
    """
    processes = []
    for file in os.listdir('/proc'):
        if file.isdigit():
            processes.append(Process(int(file)))
    return processes

class Process(object):
    """A C{Process} object represents a process with a particular PID. The process may or may not
    be running when the C{Process} object is used. It is conceivable that the C{Process} object
    does not represent the same process that was identified by the PID when the C{Process} object
    was created.
    """

    __pid = None
    __parent = None
    __commandline = None
    __env = None
    __status = None

    def __init__(self, pid):
        """Creates a C{Process} object for a given C{pid}. For internal use only.
        """
        self.__pid = pid

    def __repr__(self):
        """Returns a string describing this C{Process}.
        """
        return 'Process(%s)' % self.__pid

    def __cmp__(self, other):
        """Ranks C{Process}es by PID.
        """
        return self.__pid - other.___pid

    def __hash__(self):
        return self.__pid

    def __reduce__(self):
        # Get ready for pickling
        self._ensure_status_file_read()
        x = self.commandline
        x = self.env

    def _parent(self):
        if self._ensure_status_file_read() and not self.__parent:
            parent_pid = int(self.__status['PPid'])
            self.__parent = Process(parent_pid)
        return self.__parent

    def _descendents(self):
        """
        """
        subtree = []
        self._add_children_recursively(subtree, processes())
        return subtree

    def _state(self):
        """
        """
        state = None
        if self._ensure_status_file_read():
            state = self.__status.get('State', None)
            if state is not None:
                space = state.find(' ')
                state = state[:space]
        return state

    def _size(self):
        size = None
        if self._ensure_status_file_read():
            size = self.__status.get('VmSize', None)
            if size is not None:
                space = size.find(' ')
                assert size[space + 1:].lower() == 'kb'
                size = int(size[:space]) # chop off kB
                size *= 1024 # multiply by kB
        return size

    def _rss(self):
        rss = None
        if self._ensure_status_file_read():
            rss = self.__status.get('VmRSS', None)
            if rss is not None:
                space = rss.find(' ')
                assert rss[space + 1:].lower() == 'kb'
                rss = int(rss[:space]) # chop off kB
                rss *= 1024 # multiply by kB
        return rss

    def _commandline(self):
        if not self.__commandline:
            commandline_tokens = self._strings_file('cmdline')
            if commandline_tokens:
                self.__commandline = ' '.join(commandline_tokens)
            if self.__commandline is None:
                self.__commandline = ''
        return self.__commandline

    def _env(self):
        if not self.__env:
            env_map = self._strings_file('environ')
            if env_map:
                self.__env = {}
                for key_value_string in env_map:
                    eq = key_value_string.find('=')
                    key = key_value_string[:eq].strip()
                    value = key_value_string[eq + 1:].strip()
                    if key:
                        self.__env[key] = value
        return self.__env

    pid = property(lambda self: self.__pid, doc = 'The PID of this C{Process}.')
    parent = property(_parent, doc = 'The parent of this C{Process}. Returns a C{Process} object.')
    descendents = property(_descendents, doc = 'A list containing C{Process} objects corresponding to the descendents of this C{Process}, (children, grandchildren, etc.)')
    state = property(_state, doc = 'The state of this C{Process}.')
    size = property(_size, doc = 'The VM size of this C{Process}.')
    rss = property(_rss, doc = 'The VM RSS of this C{Process}.')
    commandline = property(_commandline, doc = 'The command-line used to create this C{Process}.')
    env = property(_env, doc = 'A map describing the environment in effect during the creation of this C{Process}.')
    
    def kill(self, signal = None):
        """Send the indicated C{signal} to this process.
        """
        if signal:
            os.system('kill -%s %s' % (signal, self.pid))
        else:
            os.system('kill %s' % (self.pid))

    def _ensure_status_file_read(self):
        exists = True
        if self.__status is None:
            self.__status = {}
            try:
                status_filename = '%s/status' % self._procdir()
                status_file = open(status_filename, 'r')
                status = status_file.read().split('\n')
                status_file.close()
                for key_value_string in status:
                    colon = key_value_string.find(':')
                    key = key_value_string[:colon].strip()
                    value = key_value_string[colon + 1:].strip()
                    self.__status[key] = value
            except IOError:
                exists = False
        return exists

    def _add_children_recursively(self, subtree, processes):
        children = []
        for process in processes:
            if process.parent and process.parent.pid == self.pid:
                children.append(process)
                process._add_children_recursively(subtree, processes)
        subtree.extend(children)

    def _strings_file(self, filename):
        strings = []
        try:
            filename = '%s/%s' % (self._procdir(), filename)
            file = open(filename, 'r')
            contents = file.read()
            file.close()
            strings = contents.split(chr(0))
        except IOError:
            pass
        return strings

    def _procdir(self):
        return '/proc/%s' % self.pid

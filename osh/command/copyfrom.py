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

"""C{copyfrom [-Crpx] FILES LOCAL_DIR}

Copies C{FILES} from each node of a cluster to
C{LOCAL_DIR}. The cluster is identified using remote execution syntax, for
example::

    osh @fred [ copyfrom /var/log/messages . ]


C{FILES} identifies files on nodes of the cluster. It must be
an absolute path, (i.e. must begin with C{'/'}) and may specify
multiple files, e.g. C{/foo/bar*/*.[0-9]}.  C{LOCAL_DIR} is a
directory on the node from which the command is being issued.

C{copyfrom} will normally populate a directory under C{LOCAL_DIR} for
each node in the cluster, creating the subdirectories if necessary.
The name of the subdirectory will be the same as the node's name,
specified in C{.oshrc}. But if C{-x} is specified, then subdirectories
will not be populated; files will be placed directly in
C{LOCAL_DIR}. The C{-x} option is supported only for single-node
clusters.
    
C{copyfrom} is implemented using C{scp}, and the following C{scp} flags are supported:
    - C{-C}: enable compression.
    - C{-r}: recursive copy
    - C{-p}: preserve modification times, access times, and modes.
"""

import os

import osh.args
import osh.core
import osh.spawn

Spawn = osh.spawn.Spawn
Option = osh.args.Option

# CLI
def _copyfrom():
    return _CopyFrom()

# API
def copyfrom(files, local_dir,
             compress = False, recursive = False, preserve = False, no_subdirs = False):
    """Copies C{files} from each node of the specified C{cluster} to C{local_dir}.
    If C{no_subdirs} is False, then a subdirectory under C{local_dir} is created for
    each node of the cluster and the files from a node are copied to that node's subdirectory.
    If C{no_subdirs} is true, then C{cluster} must be a single-node cluster, no subdirectory
    is created, and files are copied directly into C{local_dir}. Compression is used
    for copying if C{compress} is True. Directories are copied recursively if C{recursive} is
    True. File attributes are preserved if C{preserve} is True.
    """
    args = []
    if compress:
        args.append(Option('-C'))
    if recursive:
        args.append(Option('-r'))
    if preserve:
        args.append(Option('-p'))
    if no_subdirs:
        args.append(Option('-x'))
    return _CopyFrom().process_args(*args)

class _CopyFrom(osh.core.RunLocal):

    # state

    _local_dir = None
    _file = None
    _scp_options = None
    _use_subdirs = None


    # object interface
    
    def __init__(self):
        osh.core.RunLocal.__init__(self, 'Crpx', (2, 2))

    # BaseOp interface
    
    def doc(self):
        return __doc__

    def setup(self):
        args = self.args()
        scp_options = ''
        for option in 'Crp':
            if args.flag('-' + option):
                scp_options += option
        if scp_options:
            self._scp_options = '-' + scp_options
        else:
            self._scp_options = ''
        self._use_subdirs = not args.flag('-x')
        if args.has_next():
            self._file = args.next_string()
        if args.has_next():
            self._local_dir = args.next_string()
        if not self._file or not self._local_dir or args.has_next():
            self.usage()
        if not self._file.startswith('/'):
            self.usage()

    # Generator interface

    def execute(self):
        host = self.thread_state
        target_dir = self._local_dir
        if self._use_subdirs:
            target_dir += '/' + host.name
        try:
            os.makedirs(target_dir)
        except OSError:
            pass
        _copydown(host.user,
                  host.identity,
                  host.address,
                  self._file,
                  target_dir,
                  self._scp_options)

def _copydown(user, identity, host, file, local_dir, options):
    if identity:
        scp_command = 'scp %s -i %s %s@%s:%s %s' % (options,
                                                    identity,
                                                    user,
                                                    host,
                                                    file,
                                                    local_dir)
    else:
        scp_command = 'scp %s %s@%s:%s %s' % (options,
                                              user,
                                              host,
                                              file,
                                              local_dir)
    Spawn(scp_command, None, None, None).run()

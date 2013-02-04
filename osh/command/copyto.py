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

"""C{copyto [-rpC] FILE ... REMOTE_DIR}

Copies C{FILE}s to C{REMOTE_DIR} on each node of a cluster.
The cluster is identified using remote execution syntax, for example::

    osh @fred [ copyto log.properties /opt/foobar/config ]

C{REMOTE_DIR} must be an absolute path, (i.e. must begin with C{'/'}).

C{copyto} is implemented using C{scp}, and the following C{scp} flags
are supported:
    - C{-C}: enable compression.
    - C{-r}: recursive copy
    - C{-p}: preserve modification times, access times, and modes.
"""

import osh.core
import osh.spawn

Spawn = osh.spawn.Spawn

# CLI
def _copyto():
    return _CopyTo()

# API
def copyto(files, compress = False, recursive = False, preserve = False):
    """Copies files to each node of the specified C{cluster}. The last elements
    of C{files} is the target directory on each node. The preceding elements are
    the local files to be copied. Compression is used  for copying if C{compress}
    is True. Directories are copied recursively if C{recursive} is
    True. File attributes are preserved if C{preserve} is True.
    """
    args = []
    if compress:
        args.append(Option('-C'))
    if recursive:
        args.append(Option('-r'))
    if preserve:
        args.append(Option('-p'))
    return _CopyTo().process_args(*args)

class _CopyTo(osh.core.RunLocal):

    # state

    _remote_dir = None
    _files = None
    _scp_options = None


    # object interface
    
    def __init__(self):
        osh.core.RunLocal.__init__(self, 'rpC', (2, None))


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
        files = args.remaining()
        if len(files) < 2:
            self.usage()
        self._remote_dir = files[-1]
        if not self._remote_dir.startswith('/'):
            self.usage()
        self._files = files[:-1]

    # Generator interface

    def execute(self):
        host = self.thread_state
        _copyup(self._files,
                host.user,
                host.identity,
                host.address,
                self._remote_dir,
                self._scp_options)

def _copyup(files, user, identity, host, remote_dir, options):
    if isinstance(files, list) or isinstance(files, tuple):
        files = ' '.join(files)
    if identity:
        scp_command = 'scp %s -i %s %s %s@%s:%s' % (options,
                                                    identity,
                                                    files,
                                                    user,
                                                    host,
                                                    remote_dir)
    else:
        scp_command = 'scp %s %s %s@%s:%s' % (options, files, user, host, remote_dir)
    Spawn(scp_command, None, None, None).run()

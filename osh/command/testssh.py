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

"""C{testssh}

Determines if ssh connectivity to a cluster is working. 
Can only be run against a cluster, e.g. C{osh @mycluster [ testssh ] $}.

ssh is configured correctly if each node name is printed, along with the output
from the test command, C{hello}, for example::

    ('115', 'hello')
    ('116', 'hello')
    ('117', 'hello')

If your ssh agent is set up properly, then you may see some additional
output the first time you contact a cluster, e.g.
C{Warning: Permanently added '192.168.140.115' (RSA) to the list of known hosts.}
"""

import os

import osh.args
import osh.core
from osh.util import ssh, remove_crlf
from osh.error import stderr_handler

# CLI
def _testssh():
    return _TestSSH()

# API
def testssh():
    """Determines if ssh connectivity to a cluster is working. 
    Can only be run against a cluster, e.g. C{osh(remote('mycluster', testssh()), out())}.
    ssh is configured correctly if each node name is printed, along with the output
    from the test command, C{hello}, e.g. C{('115', 'hello'), ('116', 'hello'), 
    ('117', 'hello')}.
    If your ssh agent is set up properly, then you may see some additional
    output the first time you contact a cluster, e.g.  C{Warning:
    Permanently added '192.168.140.115' (RSA) to the list of known hosts.}
    """
    return _TestSSH().process_args()

class _TestSSH(osh.core.RunLocal):

    # object interface
    
    def __init__(self):
        osh.core.RunLocal.__init__(self, '', (0, 0))

    # BaseOp interface
    
    def doc(self):
        return __doc__

    def setup(self):
        pass

    # Generator interface

    def execute(self):
        host = self.thread_state
        output, errors = ssh(host.user, host.identity, host.address, 'echo hello')
        for line in output:
            self.send(remove_crlf(line))
        for line in errors:
            stderr_handler(line, self, None)

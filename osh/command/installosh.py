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

"""C{installosh INSTALL_DIRECTORY [OSH_CONFIG_FILE]}

Installs osh on a cluster. The cluster is identified using
remote execution syntax, for example::

    osh @fred [ installosh /usr/local/lib/python2.6/site-packages ]

C{INSTALL_DIRECTORY} specifies the installation directory on each node
of the cluster. On each node of the cluster, a C{.oshrc} files is
created in the home directory of the user specified for
C{CLUSTER}. This file is copied from C{OSH_CONFIG_FILE}, if
specified. Otherwise, C{~/.oshrc} is copied.

Not available through the API.
"""

import os
import os.path
import sys
import threading

import osh.core
import osh.config
import osh.cluster
import osh.util

import progtrack

ssh = osh.util.ssh
scp = osh.util.scp

_DISTRIBUTION_FILENAME = 'osh.tgz'
_CONFIG_FILE = '.oshrc'
_REMOTE_STAGING_DIR = '/tmp/osh'
_REMOTE_INSTALL_SCRIPT = 'remoteinstall.py'

# CLI
def _installosh():
    return _InstallOsh()

class _InstallOsh(osh.core.RunLocal):

    _local_osh_dir = None
    _remote_install_dir = None
    _config_file = None

    # object interface

    def __init__(self):
        osh.core.RunLocal.__init__(self, '', (1, 2))

    # BaseOp interface
    
    def doc(self):
        return __doc__

    def create_command_state(self, oshthreads):
        ui = progtrack.ProgressTrackingUI('installosh')
        ui.add_column('host', 25)
        ui.add_column(['create', 'staging dir'], 10)
        ui.add_column(['copy', 'package'], 10)
        ui.add_column(['copy', 'installer'], 10)
        ui.add_column(['run', 'installer'], 10)
        ui.add_column(['copy', 'conf file'], 10)
        for thread in oshthreads:
            host = thread.state
            ui.add_row(host.name)
        return ui

    def setup(self):
        args = self.args()
        self._remote_install_dir = args.next_string()
        if args.has_next():
            self._config_file = args.next_string()
        else:
            self._config_file = '%s/%s' % (os.environ['HOME'], _CONFIG_FILE)
        self.find_local_osh_dir()
            
    # Generator interface

    def execute(self):
        # UI object actually starts only on first call to start, ignores subsequent calls.
        self.ui.start() 
        try:
            self.create_install_package()
            self.install()
        finally:
            self.delete_install_package()
            self.ui.stop()


    # internals

    ui = property(lambda self: self.command_state())

    host = property(lambda self: self.thread_state)

    def install(self):
        host = self.host
        ui = self.ui
        stage = 0
        try:
            # Remove existing remote install directory directory
            stage += 1
            ssh(host.user,
                host.identity,
                host.address,
                '"rm -rf %s"' % _REMOTE_STAGING_DIR)
            # Create remote install directory
            ssh(host.user,
                host.identity,
                host.address,
                '"mkdir %s"' % _REMOTE_STAGING_DIR)
            ui.ok(host.name, stage)
            # Copy package to remote install directory
            stage += 1
            scp(host.user,
                host.identity,
                host.address,
                None,
                '/tmp/%s' % _DISTRIBUTION_FILENAME,
                _REMOTE_STAGING_DIR)
            ui.ok(host.name, stage)
            # Copy remoteinstall script to remote install directory
            stage += 1
            scp(host.user,
                host.identity,
                host.address,
                None,
                '%s/command/%s' % (self._local_osh_dir, _REMOTE_INSTALL_SCRIPT),
                _REMOTE_STAGING_DIR)
            ssh(host.user,
                host.identity,
                host.address,
                'chmod a+x %s/%s' % (_REMOTE_STAGING_DIR, _REMOTE_INSTALL_SCRIPT))
            ui.ok(host.name, stage)
            # Run remoteinstall script
            stage += 1
            ssh(host.user,
                host.identity,
                host.address,
                '"%s/%s %s %s %s"' % (_REMOTE_STAGING_DIR, 
                                      _REMOTE_INSTALL_SCRIPT,
                                      _REMOTE_STAGING_DIR,
                                      _DISTRIBUTION_FILENAME,
                                      self._remote_install_dir))
            ui.ok(host.name, stage)
            # Copy config file to home directory unless one already exists
            stage += 1
            ls_oshrc, errors = ssh(host.user,
                                   host.identity,
                                   host.address,
                                   '"ls /%s/%s"' % (host.user, _CONFIG_FILE))
            if len(ls_oshrc) == 0:
                scp(host.user,
                    host.identity,
                    host.address,
                    None,
                    self._config_file,
                    '~')
            ui.ok(host.name, stage)
        except:
            (exc_type, exc_value, exc_traceback) = sys.exc_info()
            message = str(exc_value).strip()
            ui.error(host.name, stage, message)

    def create_install_package(self):
        os.system('cd %s; find . -type f | egrep "\.py$" | xargs tar czf /tmp/%s' % 
                  (self._local_osh_dir, _DISTRIBUTION_FILENAME))

    def delete_install_package(self):
        os.system('rm -rf /tmp/%s' % _DISTRIBUTION_FILENAME)

    def find_local_osh_dir(self):
        self._local_osh_dir = None
        for path in sys.path:
            dir = '%s/osh' % path
            if os.path.exists(dir) and os.path.isdir(dir):
                self._local_osh_dir = dir
        if self._local_osh_dir is None:
            raise Exception('osh directory not found in sys.path!')

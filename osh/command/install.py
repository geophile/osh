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

"""C{install [-d INSTALL_DIRECTORY] [-p PACKAGE] DIRECTORY}

C{install [-d INSTALL_DIRECTORY] [-p PACKAGE] PYTHON_MODULE ...}

Installs Python modules a cluster. The cluster is identified using
remote execution syntax, for example::

    osh @fred [ install ~/foobar.py ]

If C{-d} is not
specified, then installation is to the standard site-packages
directory (e.g. /usr/lib/python2.4/site-packages). Otherwise,
installation goes to C{INSTALL_DIRECTORY}. (C{INSTALL_DIRECTORY}
replaces the entire path, not just the C{/usr} or C{/usr/lib} part of
the path.)  The modules are identified as individual
C{PYTHON_MODULE}s, (i.e. filenames ending in C{.py}), or as a
C{DIRECTORY} containing the modules of interest. In the latter case,
the contents of sub-directories will be copied also, as sub-packages
of C{PACKAGE}.

Modules are installed into the remote C{site-packages} directory, in
the subdirectory specified by C{PACKAGE}, (or in C{site-packages}
directly, if C{PACKAGE} is omitted).


For example, to install the local C{foo.bar} package on cluster
C{fred}::

    osh @fred [ install -p foo.bar ~/myproject/foo/bar ]

To install a single module, C{xyz}, directly in C{site-packages}::

    osh @fred [ install ~/myproject/util/xyz.py ]

Not available through the API.
"""

import os
import os.path
import sys

import osh.core
import osh.util

import progtrack

ssh = osh.util.ssh
scp = osh.util.scp

# CLI
def _install():
    return _Install()

class _Install(osh.core.RunLocal):

    _install_dir = None
    _package = None
    _directory = None
    _modules = None


    # object interface

    def __init__(self):
        osh.core.RunLocal.__init__(self, 'd:p:', (1, None))

    # BaseOp interface
    
    def doc(self):
        return __doc__

    def create_command_state(self, oshthreads):
        ui = progtrack.ProgressTrackingUI('install')
        ui.add_column('host', 25)
        ui.add_column(['find', 'install dir'], 12);
        ui.add_column('installed', 12)
        for thread in oshthreads:
            host = thread.state
            ui.add_row(host.name)
        return ui

    def setup(self):
        args = self.args()
        self._install_dir = args.string_arg('-d')
        self._package = args.string_arg('-p')
        sources = args.remaining()
        if len(sources) == 1 and os.path.isdir(sources[0]):
            self._directory = sources[0]
        else:
            for source in sources:
                if not source.endswith('.py'):
                    self.usage()
            self._modules = [x for x in sources]

    # Generator interface

    def execute(self):
        # UI object actually starts only on first call to start, ignores subsequent calls.
        if self.thread_state:
            self.ui.start()
            try:
                self.install_remote()
            finally:
                self.ui.stop()
        else:
            self.install_local()


    # internals

    ui = property(lambda self: self.command_state())

    host = property(lambda self: self.thread_state)

    def install_local(self):
        install_dir = self.install_dir((sys.prefix,) + sys.version_info[0:2])
        if self._directory:
            flags = '-Rp'
            sources = '%s/*' % self._directory
        elif self._modules:
            flags = '-p'
            sources = ' '.join(self._modules)
        else:
            assert False
        os.system('cp %s %s %s' % (flags, sources, install_dir))

    def install_remote(self):
        host = self.host
        ui = self.ui
        try:
            # Find install directory
            stage = 1
            version_command = ""
            output, errors = ssh(self.user(),
                                 host.identity,
                                 host.address,
                                 "python -c 'import sys; print (sys.prefix,) + sys.version_info[0:2]'")
            package_dir = self.package_dir()
            install_dir = self.install_dir(eval(output[0])) + '/' + package_dir
            if package_dir != '':
                ssh(self.user(),
                    host.identity,
                    host.address,
                    'mkdir -p %s' % install_dir)                     
            ui.ok(host.name, stage)
            # Copy files
            stage = 2
            if self._directory:
                flags = '-rp'
                sources = '%s/*' % self._directory
            elif self._modules:
                flags = '-p'
                sources = ' '.join(self._modules)
            else:
                assert False
            scp(self.user(), host.identity, host.address, flags, sources, install_dir)
            ui.ok(host.name, stage)
        except:
            (exc_type, exc_value, exc_traceback) = sys.exc_info()
            message = str(exc_value).strip()
            ui.error(host.name, stage, message)

    def install_dir(self, install_info):
        if self._install_dir:
            return self._install_dir
        else:
            return '/%s/lib/python%s.%s/site-packages' % install_info

    def package_dir(self):
        if self._package:
            path = self._package.replace('.', '/')
        else:
            path = ''
        return path

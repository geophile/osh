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

"""C{ls [-01rfds] [FILENAME_PATTERN ...]}

Generates a stream of objects of type C{osh.file.File}. Each
C{FILENAME_PATTERN} is expanded as a Unix "glob" pattern. If no
C{FILENAME_PATTERN}s are specified, then the files in the current
directory are output.  If C{-0} (that's a zero) is specified, then
only files matching the specified C{FILENAME_PATTERN}s are output; any
qualifying directories are not explored. If C{-1} (that's the digit
one, not the letter L) is specified, then files are listed and
directories are expanded to one level.  If C{-r} is specified, then
directories are recursively explored.  At most one of these flags may
be specified. If none of these flags are specified, then the behavior
defaults to C{-1}.

If C{-f} is specified, files are listed. If C{-d} is specified,
directories are listed. If C{-s} is specified, symlinks are listed.
Combinations of these flags are permitted. If none of these flags are
specified, then files, directories and symlinks are listed.

Symlinks to directories are not explored."""

import os
import os.path
import glob

import osh.core
import osh.args
import osh.file

Option = osh.args.Option
File = osh.file.File

# CLI
def _ls():
    return _Ls()

# API
def ls(paths,
       depth_0 = False,
       depth_1 = False,
       recursive = False,
       file = False,
       dir = False,
       link = False):
    """Generates a stream of objects of type C{osh.file.File}. C{paths} may be a single
    path or a sequence of paths
    Each path in C{paths}
    is expanded as a Unix "glob" pattern. If no path is specified,
    then the files in the current directory are output.
    If C{depth_0} is True, then only files matching the specified pathss are
    output; any qualifying directories are not explored. If C{depth_1} is True,
    then behavior is as for C{depth_0} except that files in qualifying directories
    are output as well. If C{recursive} is True, then directories are recursively explored.
    At most one of the last three arguments may be True. If all are False,
    then C{depth_1} behavior is obtained. Files are listed if and only if C{file} is
    true. Directories are listed if and only if C{dir} is true. Symlinks are listed
    if and only if C{link} is true. If C{file}, C{dir} and C{link} are all false,
    then files, directories and symlinks are listed. Symlinks to directories are
    not explored.
    """
    args = []
    if depth_0:
        args.append(Option('-0'))
    if depth_1:
        args.append(Option('-1'))
    if recursive:
        args.append(Option('-r'))
    if file:
        args.append(Option('-f'))
    if dir:
        args.append(Option('-d'))
    if link:
        args.append(Option('-s'))
    if isinstance(paths, str):
        paths = [paths]
    args.extend(paths)
    return _Ls().process_args(*args)

class _Ls(osh.core.Generator):

    _recursion = None
    _patterns = None
    _lister = None
    _list_file = None
    _list_dir = None
    _list_link = None

    # object interface

    def __init__(self):
        osh.core.Generator.__init__(self, '01rfds', (0, None))

    # BaseOp interface
    
    def doc(self):
        return __doc__

    def setup(self):
        args = self.args()
        depth0 = args.flag('-0')
        depth1 = args.flag('-1')
        recursive = args.flag('-r')
        count = 0
        if depth0:
            count += 1
            self._lister = _Lister0(self)
        if depth1:
            count += 1
            self._lister = _Lister1(self)
        if recursive:
            count += 1
            self._lister = _ListerRecursive(self)
        if count == 0:
            self._lister = _Lister1(self)
        elif count > 1:
            self.usage()
        self._list_file = args.flag('-f')
        self._list_dir = args.flag('-d')
        self._list_link = args.flag('-s')
        if not (self._list_file or self._list_dir or self._list_link):
            self._list_file = True
            self._list_dir = True
            self._list_link = True
        self._patterns = args.remaining()
        if len(self._patterns) == 0:
            self._patterns = ['.']

    # Generator interface
    
    def execute(self):
        for pattern in self._patterns:
            for path in glob.glob(pattern):
                file = File(path)
                self._lister.list(path)

class _Lister(object):

    def __init__(self, ls):
        self._ls = ls

    def send(self, file):
        ls = self._ls
        if (file.isfile and ls._list_file or
            file.isdir and ls._list_dir or
            file.islink and ls._list_link):
            ls.send(file)
        
class _Lister0(_Lister):

    def __init__(self, ls):
        _Lister.__init__(self, ls)

    def list(self, path):
        self.send(File(path))

class _Lister1(_Lister):

    def __init__(self, ls):
        _Lister.__init__(self, ls)

    def list(self, path):
        file = File(path)
        self.send(file)
        if file.isdir:
            for filename in os.listdir(path):
                file = File(path, filename)
                self.send(file)

class _ListerRecursive(_Lister):

    def __init__(self, ls):
        _Lister.__init__(self, ls)

    def list(self, path):
        def visit(lister, dirname, filenames):
            dir = File(dirname)
            lister.send(dir)
            if dir.islink:
                # Prevent exloring link
                del filenames[:]
            else:
                for filename in filenames:
                    file = File(dirname, filename)
                    if not file.isdir:
                        lister.send(file)
                    # else: Will be send when the subdir is visited.
        if os.path.isdir(path) and not os.path.islink(path):
            os.path.walk(path, visit, self)
        else:
            self.send(File(path))

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

"""Represents a file or directory on the local host.
"""

import os
import pickle

import osh.util

DIR_MASK = 040000
FILE_MASK = 0100000
LINK_MASK = 0120000
FILE_TYPE_MASK = DIR_MASK | FILE_MASK | LINK_MASK

class File(str):

    _os_stat = None

    def __new__(self, dir, file = None):
        if file is None:
            path = dir
        else:
            path = os.path.join(dir, file)
        return str.__new__(self, path)
    
    def __init__(self, dir, file = None):
        self._dir = dir
        self._file = file

    def _stat(self):
        if self._os_stat is None:
            self._os_stat = os.lstat(self.abspath)
        return self._os_stat

    def _abspath(self):
        if self._file:
            return os.path.join(self._dir, self._file)
        else:
            return self._dir

    abspath = property(lambda self: os.path.abspath(self),
                       doc = """Absolute path to this file.""")
    stat = property(lambda self: self._stat(),
                    doc = """Information on this file, as returned by C{os.stat}.""")
    mode = property(lambda self: self._stat()[0],
                    doc = """mode of this file.""")
    inode = property(lambda self: self._stat()[1],
                     doc = """inode of this file.""")
    device = property(lambda self: self._stat()[2],
                      doc = """device of this file.""")
    links = property(lambda self: self._stat()[3],
                     doc = """ Number of links of this file.""")
    uid = property(lambda self: self._stat()[4],
                   doc = """Owner of this file.""")
    gid = property(lambda self: self._stat()[5],
                   doc = """Owning group of this file.""")
    size = property(lambda self: self._stat()[6],
                    doc = """Size of this file (bytes).""")
    atime = property(lambda self: self._stat()[7],
                     doc = """Access time of this file.""")
    mtime = property(lambda self: self._stat()[8],
                     doc = """Modify time of this file.""")
    ctime = property(lambda self: self._stat()[9],
                     doc = """Change time of this file.""")
    isdir = property(lambda self: self.mode & FILE_TYPE_MASK == DIR_MASK,
                     doc = """True iff this file is a directory.""")
    isfile = property(lambda self: self.mode & FILE_TYPE_MASK == FILE_MASK,
                      doc = """True iff this file is neither a directory nor a symlink.""")
    islink = property(lambda self: self.mode & FILE_TYPE_MASK == LINK_MASK,
                      doc = """True iff this file is a symlink.""")

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

"""
Osh is documented in the following packages and modules:

    - B{C{osh.api}}: Non-command portions of the osh API.
    - B{C{osh.builtins}}: Builtin osh functions and classes.
    - B{C{osh.command}}: Modules implementing osh commands. Documentation covers both the command-line and application programming interfaces.
    - B{C{osh.file}}: Represents files.
    - B{C{osh.function}}: Many osh commands (e.g. C{f}, C{select}) take functions as arguments. C{osh.function} has no public interface, but the documentation of this module describes the use of functions in both the command-line and application programming interfaces.
    - B{C{osh.process}}: Represents currently running processes (Linux only).
    - B{C{osh.trace}}: Trace osh internals.

"""

__all__ = [
    'api',
    'apiparser',
    'args',
    'cliparser',
    'config',
    'core',
    'function',
    'loader',
    'spawn',
    'tpg'
    ]

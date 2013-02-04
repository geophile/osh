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

"""C{sh COMMAND}

Spawns a process and executes C{COMMAND}.  Occurrences of formatting
directives (e.g. C{%s}) will be replaced by input values.  Each line
of C{stdout} is sent to the output stream. Each line of C{stderr} is
handled by the osh stderr handler, (the default handler prints to
osh's stderr).
"""

import osh.core
import osh.error
import osh.spawn
import osh.util

Spawn = osh.spawn.Spawn
LineOutputConsumer = osh.spawn.LineOutputConsumer
remove_crlf = osh.util.remove_crlf

# CLI
def _sh():
    return _Sh()

# API
def sh(command):
    """Spawns a process and executes C{command}.  Occurrences of formatting
    directives (e.g. C{%s}) will be replaced by input values.  Each line
    of C{stdout} is sent to the output stream. Each line of C{stderr} is
    handled by the osh stderr handler, (the default handler prints to
    osh's stderr).
    """
    return _Sh().process_args(command)

class _Sh(osh.core.Generator):

    # state

    _command = None


    # object interface
    
    def __init__(self):
        osh.core.Generator.__init__(self, '', (1, 1))


    # BaseOp interface
    
    def doc(self):
        return __doc__

    def setup(self):
        args = self.args()
        if args.has_next():
            self._command = args.next_string()
            if args.has_next():
                self.usage()
        else:
            self.usage()

    def receive(self, object):
        boundCommand = self._bind(object)
        self._execute_command(boundCommand, object)

    # remote compile-time interface

    def setCommand(self, command):
        self._command = command
        return self


    # Generator interface
    
    def execute(self):
        self._execute_command(self._command, None)

    # For use by this class

    def _bind(self, input):
        command = self._command
        if type(input) != tuple:
            input = (input,)
        for value in input:
            command = command.replace('%s', str(value), 1)
        return command

    def _execute_command(self, command, input):
        process = Spawn(command,
                        None,
                        LineOutputConsumer(lambda line: self.send(remove_crlf(line))),
                        LineOutputConsumer(lambda line:
                                               osh.error.stderr_handler(line,
                                                                        self,
                                                                        input)))
        process.run()

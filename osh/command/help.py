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

"""C{help [OSH_COMMAND]}

If C{OSH_COMMAND} is specified, print usage information for the named osh command. Otherwise, list
the builtin commands.
"""

import sys

import osh.core

# CLI
def _help():
    return _Help()

# API
def help(osh_command = None):
    """Prints usage information on osh commands. If C{osh_command} is specified,
    print usage information for the named osh command. Otherwise, list the builtin commands.
    """
    return _Help()

class _Help(osh.core.Generator):

    _command_name = None


    # object interface

    def __init__(self):
        osh.core.Generator.__init__(self, '', (0, 1))


    # OshCommand interface
    
    def doc(self):
        return __doc__

    def setup(self):
        args = self.args()
        if args.has_next():
            self._command_name = args.next_string()
            if args.has_next():
                self.usage()

    # Generator interface
    
    def execute(self):
        if self._command_name:
            try:
                top_level_module = __import__('osh.command.' + self._command_name)
                module = getattr(top_level_module, 'command')
                module = getattr(module, self._command_name)
                print _remove_epydoc_markup(module.__doc__)
            except Exception, e:
                print >>sys.stderr, "Can't find documentation for %s: %s" % (self._command_name, e)
        else:
            import osh.command
            import osh.command.help
            print _remove_epydoc_markup(__doc__)
            print 'Builtin commands:'
            for command in osh.command.cli:
                print '\t', command

# Translation of epydoc markup to plain text. This is pretty weak -- it doesn't
# account for nested markup or markup inside quotes.

_MARKUP = ['B{', 'C{', 'i{', '::']

def _nearest_markup(text, start):
    nearest_markup = None
    nearest_start = len(text)
    for i in xrange(len(_MARKUP)):
        markup = _MARKUP[i]
        position = text.find(markup, start)
        if position != -1 and position < nearest_start:
            nearest_markup = markup
            nearest_start = position
    if nearest_markup:
        if '{' in nearest_markup:
            markup_end = text.find('}', nearest_start)
            assert markup_end > nearest_start
        else:
            markup_end = None
        return nearest_start, nearest_markup, markup_end
    else:
        return None, None, None

def _remove_epydoc_markup(text):
    plain = []
    plain_start = 0
    while plain_start < len(text):
        markup_start, markup, markup_end = _nearest_markup(text, plain_start)
        if markup_start is None:
            # No more markup
            plain.append(text[plain_start :])
            plain_start = len(text)
        else:
            # Get everything up to markup
            plain.append(text[plain_start : markup_start])
            if '{' in markup:
                # If markup is x{...} get text between the braces.
                assert markup_end is not None, markup_end
                plain.append(text[markup_start + len(markup) : markup_end])
                plain_start = markup_end + 1
            else: # must be ::
                plain.append(':')
                plain_start = markup_start + len(markup)            
    return ''.join(plain)

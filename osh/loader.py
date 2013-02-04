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

import config

def load_and_create(name):
    for package in (['command', 'command.sqladapter'] + list(config.oshpath)):
        try:
            module_name = '%s.%s' % (package, name)
            return _import_and_create(module_name, name)
        except ImportError, e:
            pass
    # If we got here, then name isn't in any declared or implied package.
    # See if it's available unqualified. (Don't do this check first to avoid
    # picking up osh commands that clash with standard python modules, e.g. select.)
    try:
        return _import_and_create(name, name)
    except ImportError:
        raise ImportError("Could not find %s as a python or osh builtin, or on osh.path %s" %
                          (name, config.oshpath))

def _import_and_create(module_name, name):
    exec('import %s' % module_name)
    constructor_call = '%s._%s()' % (module_name, name)
    return eval(constructor_call)

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

import core
import api

def _is_base_op(x):
    return isinstance(x, core.BaseOp)

def _is_sequence(x):
    return isinstance(x, list) or isinstance(x, tuple)

def _is_return_list(x):
    return isinstance(x, api._ReturnList)

def _op(x):
    if _is_base_op(x):
        op = x
    elif _is_sequence(x):
        op = _sequence_op(x)
    elif _is_return_list(x):
        raise IllegalOshCommand('return_list() only permitted as last command')
    else:
        raise IllegalOshCommand('%s is not an osh command.' % x)
    return op

def _sequence_op(sequence):
    pipeline = core.Pipeline()
    for x in sequence:
        pipeline.append_op(_op(x))
    return pipeline

class IllegalOshCommand(Exception):

    def __init__(self, garbage):
        self._garbage = garbage

    def __str__(self):
        return 'Illegal osh command or sub-command: %s' % self._garbage

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

import sys
import threading

# "Private" name (with leading underscore) so that epydoc doesn't document the class
class _OshThread(threading.Thread):

    _owner = None
    _pipeline = None
    _thread_state = None
    _terminating_exception = None
    
    def __init__(self, owner, thread_state, pipeline):
        threading.Thread.__init__(self)
        self._owner = owner
        self._pipeline = pipeline
        self._thread_state = thread_state
        pipeline.set_thread_state(thread_state)

    def __repr__(self):
        return 'oshthread(%s)' % self._thread_state

    state = property(lambda self: self._thread_state)
    pipeline = property(lambda self: self._pipeline)
    terminating_exception = property(lambda self: self._terminating_exception)
            
    def run(self):
        try:
            # Don't call self._pipeline.setup(): Done by _Fork.execute
            self._pipeline.execute()
        except Exception, e:
            self._terminating_exception = e


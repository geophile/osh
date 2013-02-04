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

"""For API usage only, (for CLI use C{osh @CLUSTER [ ... ]} syntax instead.)
"""

import fork

# API
def remote(cluster, command, merge_key = None):
    """Executes C{command} remotely on each node of C{cluster}. Execution on all nodes is
    done in parallel. If C{merge_key} is specified, then
    the inputs of each thread are expected to be ordered by the C{merge_key}. The sequences
    from the threads
    are then merged into a single sequence using the C{merge_key}.
    (This function is identical to C{fork}, except that the first argument is required to
    identify a cluster.)
    """
    op = fork.fork(cluster, command, merge_key)
    op._set_cluster_required(True)
    return op
        

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

"""This module contains miscellaneous functions builtin to osh.
See also the C{osh.process} module for other builtins.
"""

import config
from core import add_to_namespace
from cluster import cluster_named

#----------------------------------------------------------------------

# processes

from process import processes

add_to_namespace('processes', processes)

#----------------------------------------------------------------------

# ifelse

def ifelse(predicate, if_true, if_false):
    """Returns C{if_true} if C{predicate} is true, C{if_false} otherwise.
    Both C{if_true} and C{if_false} are evaluated unconditionally.
    (This function is provided because the Python equivalent, the if expression,
    is not present prior to release 2.5.)
    """
    if predicate:
        return if_true
    else:
        return if_false

add_to_namespace('ifelse', ifelse)

#----------------------------------------------------------------------

# hosts

def hosts(cluster_name):
    """Returns the value of C{cluster_name}'s C{hosts} configuration value,
    as specified in C{.oshrc}. Returns a map containing entries
    in which the key is the node's name, and the value is the node's
    IP address or DNS name.
    """
    map = {}
    cluster = cluster_named(cluster_name)
    if cluster:
        for host in cluster.hosts:
            map[host.name] = host.address
        return map
    else:
        return None

add_to_namespace('hosts', hosts)

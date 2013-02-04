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

_clusters = {}

class Host(object):

    _name = None
    _address = None
    _user = None
    _identity = None
    _db_profile = None
    _schema = None

    def __init__(self, name, address, user, identity, db_profile):
        self._name = name
        self._address = address
        self._user = user
        self._identity = identity
        self._db_profile = db_profile

    def __repr__(self):
        if self._schema:
            return "'%s(%s)'" % (self._name, self._schema)
        else:
            return "'%s'" % self._name

    def _set_schema(self, schema):
        self._schema = schema

    name = property(lambda self: self._name)
    address = property(lambda self: self._address)
    user = property(lambda self: self._user)
    identity = property(lambda self: self._identity)
    db_profile = property(lambda self: self._db_profile)
    schema = property(lambda self: self._schema, _set_schema)

class Cluster(object):

    _name = None
    _user = None
    _hosts = None

    def __init__(self, name, user, hosts, pattern):
        self._name = name
        self._user = user
        if pattern:
            self._hosts = [host for host in hosts if pattern in host.name]
        else:
            self._hosts = [host for host in hosts]

    def __str__(self):
        return self._name

    name = property(lambda self: self._name)
    user = property(lambda self: self._user)
    hosts = property(lambda self: self._hosts)

def cluster_named(cluster_name, pattern = None):
    global _clusters
    cluster = _clusters.get((cluster_name, pattern), None)
    if cluster is None:
        # user
        config_user = config.config_value('remote', cluster_name, 'user')
        if config_user is None:
            config_user = 'root'
        # identity
        config_identity = config.config_value('remote', cluster_name, 'identity')
        # hosts
        config_hosts = config.config_value('remote', cluster_name, 'hosts')
        if isinstance(config_hosts, list) or isinstance(config_hosts, tuple):
            hosts = [Host(addr, addr, config_user, config_identity, None)
                     for addr in config_hosts]
        elif isinstance(config_hosts, dict):
            hosts = []
            for name, host_spec in config_hosts.iteritems():
                addr, db_profile = _parse_host_spec(cluster_name, host_spec)
                hosts.append(Host(name, addr, config_user, config_identity, db_profile))
        else:
            return None
        if config_user and hosts:
            cluster = Cluster(cluster_name, config_user, hosts, pattern)
            _clusters[(cluster_name, pattern)] = cluster
        else:
            cluster = None
    return cluster

def define_cluster(name, user, hosts):
    global _clusters
    if isinstance(hosts, str):
        hosts = [hosts]
    elif isinstance(hosts, list):
        hosts = [host for host in hosts]
    elif isinstance(hosts, dict):
        hosts = hosts.copy()
    _clusters[(name, None)] = Cluster(name, user, hosts, None)

def _parse_host_spec(cluster_name, host_spec):
    addr = None
    db_profile = None
    if isinstance(host_spec, str):
        addr = host_spec
    elif isinstance(host_spec, dict):
        addr = host_spec.get('host', None)
        db_profile = host_spec.get('db_profile', None)
    if not addr:
        raise Exception(('Error in ~/.oshrc: ' +
                         'host specification in osh.remote.%s.hosts ' +
                         'must be string, or dict specifying keys "host" and ' +
                         'optionally "db_profile"') % cluster_name)
    return addr, db_profile

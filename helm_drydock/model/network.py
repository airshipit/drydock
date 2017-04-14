# Copyright 2017 AT&T Intellectual Property.  All other rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Models for helm_drydock
#
import logging

from copy import deepcopy

from helm_drydock.enum import SiteStatus
from helm_drydock.enum import NodeStatus

class NetworkLink(object):

    def __init__(self, **kwargs):
        self.log = logging.Logger('model')

        self.api_version = kwargs.get('apiVersion', '')

        if self.api_version == "v1.0":
            metadata = kwargs.get('metadata', {})
            spec = kwargs.get('spec', {})

            self.name = metadata.get('name', '')
            self.site = metadata.get('region', '')

            bonding = spec.get('bonding', {})
            self.bonding_mode = bonding.get('mode', 'none')

            # How should we define defaults for CIs not in the input?
            if self.bonding_mode == '802.3ad':
                self.bonding_xmit_hash = bonding.get('hash', 'layer3+4')
                self.bonding_peer_rate = bonding.get('peer_rate', 'fast')
                self.bonding_mon_rate = bonding.get('mon_rate', '100')
                self.bonding_up_delay = bonding.get('up_delay', '200')
                self.bonding_down_delay = bonding.get('down_delay', '200')

            self.mtu = spec.get('mtu', 1500)
            self.linkspeed = spec.get('linkspeed', 'auto')

            trunking = spec.get('trunking', {})
            self.trunk_mode = trunking.get('mode', 'none')

            self.native_network = spec.get('default_network', '')
        else:
            self.log.error("Unknown API version %s of %s" %
                (self.api_version, self.__class__))
            raise ValueError('Unknown API version of object')

    def get_name(self):
        return self.name

class Network(object):

    def __init__(self, **kwargs):
        self.log = logging.Logger('model')

        self.api_version = kwargs.get('apiVersion', '')

        if self.api_version == "v1.0":
            metadata = kwargs.get('metadata', {})
            spec = kwargs.get('spec', {})

            self.name = metadata.get('name', '')
            self.site = metadata.get('region', '')

            self.cidr = spec.get('cidr', None)
            self.allocation_strategy = spec.get('allocation', 'static')
            self.vlan_id = spec.get('vlan_id', 1)
            self.mtu = spec.get('mtu', 0)

            dns = spec.get('dns', {})
            self.dns_domain = dns.get('domain', 'local')
            self.dns_servers = dns.get('servers', None)

            ranges = spec.get('ranges', [])
            self.ranges = []

            for r in ranges:
                self.ranges.append(NetworkAddressRange(self.api_version, **r))

            routes = spec.get('routes', [])
            self.routes = []

            for r in routes:
                self.routes.append(NetworkRoute(self.api_version, **r))
        else:
            self.log.error("Unknown API version %s of %s" %
                (self.api_version, self.__class__))
            raise ValueError('Unknown API version of object')

    def get_name(self):
        return self.name


class NetworkAddressRange(object):

    def __init__(self, api_version, **kwargs):
        self.log = logging.Logger('model')

        self.api_version = api_version

        if self.api_version == "v1.0":
            self.type = kwargs.get('type', None)
            self.start = kwargs.get('start', None)
            self.end = kwargs.get('end', None)
        else:
            self.log.error("Unknown API version %s of %s" %
                (self.api_version, self.__class__))
            raise ValueError('Unknown API version of object')


class NetworkRoute(object):

    def __init__(self, api_version, **kwargs):
        self.log = logging.Logger('model')

        self.api_version = api_version

        if self.api_version == "v1.0":
            self.type = kwargs.get('subnet', None)
            self.start = kwargs.get('gateway', None)
            self.end = kwargs.get('metric', 100)
        else:
            self.log.error("Unknown API version %s of %s" %
                (self.api_version, self.__class__))
            raise ValueError('Unknown API version of object')

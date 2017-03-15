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

from helm_drydock.orchestrator.enum import SiteStatus
from helm_drydock.orchestrator.enum import NodeStatus

class Site(object):

    def __init__(self, **kwargs):
        self.log = logging.Logger('model')

        if kwargs is None:
            raise ValueError("Empty arguments")

        self.api_version = kwargs.get('apiVersion', '')

        self.build = kwargs.get('build', {})

        if self.api_version == "v1.0":
            metadata = kwargs.get('metadata', {})

            # Need to add validation logic, we'll assume the input is
            # valid for now
            self.name = metadata.get('name', '')

            spec = kwargs.get('spec', {})

            self.tag_definitions = []
            tag_defs = spec.get('tag_definitions', [])

            for t in tag_defs:
                self.tag_definitions.append(
                    NodeTagDefinition(self.api_version, **t))

            self.networks = []
            self.network_links = []
            self.host_profiles = []
            self.hardware_profiles = []
            self.baremetal_nodes = []

        else:
            self.log.error("Unknown API version %s of %s" %
                (self.api_version, self.__class__))
            raise ValueError('Unknown API version of object')

    def start_build(self):
        if self.build.get('status', '') == '':
            self.build['status'] = SiteStatus.Unknown
            
    def get_network(self, network_name):
        for n in self.networks:
            if n.name == network_name:
                return n

        return None

    def get_network_link(self, link_name):
        for l in self.network_links:
            if l.name == link_name:
                return l

        return None

    def get_host_profile(self, profile_name):
        for p in self.host_profiles:
            if p.name == profile_name:
                return p

        return None

    def get_hardware_profile(self, profile_name):
        for p in self.hardware_profiles:
            if p.name == profile_name:
                return p

        return None

    def get_baremetal_node(self, node_name):
        for n in self.baremetal_nodes:
            if n.name == node_name:
                return n

        return None

    def set_status(self, status):
        if isinstance(status, SiteStatus):
            self.build['status'] = status

class NodeTagDefinition(object):

    def __init__(self, api_version, **kwargs):
        self.api_version = api_version

        if self.api_version == "v1.0":
            self.tag = kwargs.get('tag', '')
            self.definition_type = kwargs.get('definition_type', '')
            self.definition = kwargs.get('definition', '')

            if self.definition_type not in ['lshw_xpath']:
                raise ValueError('Unknown definition type in ' \
                    'NodeTagDefinition: %s' % (self.definition_type))
        else:
            self.log.error("Unknown API version %s of %s" %
                (self.api_version, self.__class__))
            raise ValueError('Unknown API version of object')
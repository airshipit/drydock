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

import helm_drydock.model as model

class DesignState(object):

	def __init__(self):
		self.sites = []
		self.networks = []
		self.network_links = []
		self.host_profiles = []
		self.hardware_profiles = []
		self.baremetal_nodes = []
		return

	def add_site(self, new_site):
		if new_site is None or not isinstance(new_site, model.Site):
			raise Exception("Invalid Site model")

		self.sites.append(new_site)

    def get_sites(self):
        return self.sites

    def get_site(self, site_name):
        for s in self.sites:
            if s.name == site_name:
                return s

        raise NameError("Site %s not found in design state" % site_name)

	def add_network(self, new_network):
		if new_network is None or not isinstance(new_network, model.Network):
			raise Exception("Invalid Network model")

		self.networks.append(new_network)

    def get_networks(self):
        return self.networks

    def get_network(self, network_name):
        for n in self.networks:
            if n.name == network_name:
                return n

        raise NameError("Network %s not found in design state" % network_name)

	def add_network_link(self, new_network_link):
		if new_network_link is None or not isinstance(new_network_link, model.NetworkLink):
			raise Exception("Invalid NetworkLink model")

		self.network_links.append(new_network_link)

    def get_network_links(self):
        return self.network_links

    def get_network_link(self, link_name):
        for l in self.network_links:
            if l.name == link_name:
                return l

        raise NameError("NetworkLink %s not found in design state" % link_name)

	def add_host_profile(self, new_host_profile):
		if new_host_profile is None or not isinstance(new_host_profile, model.HostProfile):
			raise Exception("Invalid HostProfile model")

		self.host_profiles.append(new_host_profile)

    def get_host_profiles(self):
        return self.host_profiles

    def get_host_profile(self, profile_name):
        for p in self.host_profiles:
            if p.name == profile_name:
                return p

        raise NameError("HostProfile %s not found in design state" % profile_name)

	def add_hardware_profile(self, new_hardware_profile):
		if new_hardware_profile is None or not isinstance(new_hardware_profile, model.HardwareProfile):
			raise Exception("Invalid HardwareProfile model")

		self.hardware_profiles.append(new_hardware_profile)

    def get_hardware_profiles(self):
        return self.hardware_profiles

    def get_hardware_profile(self, profile_name):
        for p in self.hardware_profiles:
            if p.name == profile_name:
                return p

        raise NameError("HardwareProfile %s not found in design state" % profile_name)

	def add_baremetal_node(self, new_baremetal_node):
		if new_baremetal_node is None or not isinstance(new_baremetal_node, model.BaremetalNode):
			raise Exception("Invalid BaremetalNode model")

		self.baremetal_nodes.append(new_baremetal_node)

    def get_baremetal_nodes(self):
        return self.baremetal_nodes

    def get_baremetal_node(self, node_name):
        for n in self.baremetal_nodes:
            if n.name == node_name:
                return n

        raise NameError("BaremetalNode %s not found in design state" % node_name)

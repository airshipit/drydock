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

	def add_network(self, new_network):
		if new_network is None or not isinstance(new_network, model.Network):
			raise Exception("Invalid Network model")

		self.networks.append(new_network)

	def add_network_link(self, new_network_link):
		if new_network_link is None or not isinstance(new_network_link, model.NetworkLink):
			raise Exception("Invalid NetworkLink model")

		self.network_links.append(new_network_link)

	def add_host_profile(self, new_host_profile):
		if new_host_profile is None or not isinstance(new_host_profile, model.HostProfile):
			raise Exception("Invalid HostProfile model")

		self.host_profiles.append(new_host_profile)

	def add_hardware_profile(self, new_hardware_profile):
		if new_hardware_profile is None or not isinstance(new_hardware_profile, model.HardwareProfile):
			raise Exception("Invalid HardwareProfile model")

		self.hardware_profiles.append(new_hardware_profile)

	def add_baremetal_node(self, new_baremetal_node):
		if new_baremetal_node is None or not isinstance(new_baremetal_node, model.BaremetalNode):
			raise Exception("Invalid BaremetalNode model")

		self.baremetal_nodes.append(new_baremetal_node)



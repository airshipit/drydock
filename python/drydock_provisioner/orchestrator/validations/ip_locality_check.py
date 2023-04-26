# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
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
from drydock_provisioner.orchestrator.validations.validators import Validators

from netaddr import IPNetwork, IPAddress


class IpLocalityCheck(Validators):

    def __init__(self):
        super().__init__('IP Locality Check', "DD2002")

    def run_validation(self, site_design, orchestrator=None):
        """
        Ensures that each IP addresses assigned to a baremetal node is within the defined CIDR for the network. Also
        verifies that the gateway IP for each static route of a network is within that network's CIDR.
        """
        network_dict = {}  # Dictionary Format - network name: cidr

        baremetal_nodes_list = site_design.baremetal_nodes or []
        network_list = site_design.networks or []

        if not network_list:
            msg = 'No networks found.'
            self.report_warn(
                msg, [],
                'Site design likely incomplete without defined networks')
        else:
            for net in network_list:
                name = net.name
                cidr = net.cidr
                routes = net.routes or []

                cidr_range = IPNetwork(cidr)
                network_dict[name] = cidr_range

                if routes:
                    for r in routes:
                        gateway = r.get('gateway')

                        if not gateway:
                            msg = 'No gateway found for route %s.' % routes
                            self.report_error(
                                msg, [net.doc_ref],
                                diagnostic=
                                "Define a network-local gateway for the route."
                            )
                        else:
                            ip = IPAddress(gateway)
                            if ip not in cidr_range:
                                msg = (
                                    'The gateway IP Address %s is not within the defined CIDR: %s of %s.'
                                    % (gateway, cidr, name))
                                self.report_error(
                                    msg, [net.doc_ref],
                                    "Route gateways must reside on the local network. Check "
                                    "gateway IP and CIDR netmask.")
        if not baremetal_nodes_list:
            msg = 'No baremetal_nodes found.'
            self.report_warn(
                msg, [],
                "site design likely incomplete without defined networks.")
        else:
            for node in baremetal_nodes_list:
                addressing_list = node.addressing or []

                for ip_address in addressing_list:
                    ip_address_network_name = ip_address.network
                    address = ip_address.address
                    ip_type = ip_address.type

                    if ip_type != 'dhcp':
                        if ip_address_network_name not in network_dict:
                            msg = '%s is not a valid network.' \
                                  % (ip_address_network_name)
                            self.report_error(
                                msg, [node.doc_ref],
                                "Define network or correct address definition."
                            )
                        else:
                            if IPAddress(address) not in IPNetwork(
                                    network_dict[ip_address_network_name]):
                                msg = (
                                    'The IP Address %s is not within the defined CIDR: %s of %s .'
                                    % (address,
                                       network_dict[ip_address_network_name],
                                       ip_address_network_name))
                                self.report_error(
                                    msg, [node.doc_ref],
                                    "Define a valid address for this network.")

        return

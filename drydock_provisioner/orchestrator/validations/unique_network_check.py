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


class UniqueNetworkCheck(Validators):
    def __init__(self):
        super().__init__('Allowed Network Check', 'DD1007')

    def run_validation(self, site_design, orchestrator=None):
        """
        Ensures that each network name appears at most once between all NetworkLink
        allowed networks
        """
        network_link_list = site_design.network_links or []
        link_allowed_nets = {}

        for network_link in network_link_list:
            allowed_network_list = network_link.allowed_networks
            link_allowed_nets[network_link.name] = allowed_network_list

        # This checks the allowed networks for each network link against
        # the other allowed networks
        checked_pairs = []
        for network_link_name in link_allowed_nets:
            allowed_network_list_1 = link_allowed_nets[network_link_name]

            for network_link_name_2 in link_allowed_nets:
                if (network_link_name is not network_link_name_2
                        and sorted([network_link_name, network_link_name_2
                                    ]) not in checked_pairs):
                    checked_pairs.append(
                        sorted([network_link_name, network_link_name_2]))
                    allowed_network_list_2 = link_allowed_nets[
                        network_link_name_2]
                    # creates a list of duplicated allowed networks
                    duplicated_names = [
                        i for i in allowed_network_list_1
                        if i in allowed_network_list_2
                    ]

                    for name in duplicated_names:
                        msg = (
                            'Allowed network %s duplicated on NetworkLink %s and NetworkLink '
                            '%s' % (name, network_link_name,
                                    network_link_name_2))
                        self.report_error(
                            msg, [],
                            "Each network is only allowed to cross a single network link."
                        )

        node_list = site_design.baremetal_nodes or []

        for n in node_list:
            node_interfaces = n.interfaces or []
            for i in node_interfaces:
                nic_link = i.network_link
                for nw in i.networks:
                    try:
                        if nw not in link_allowed_nets[nic_link]:
                            msg = (
                                "Interface %s attached to network %s not allowed on interface link"
                                % (i.get_name(), nw))
                            self.report_error(msg, [
                                n.doc_ref
                            ], "Interfaces can only be attached to networks allowed on the network link "
                                              "connected to the interface.")
                    except KeyError:
                        msg = (
                            "Interface %s connected to undefined network link %s."
                            % (i.get_name(), nic_link))
                        self.report_error(msg, [
                            n.doc_ref
                        ], "Define the network link attached to this interface."
                                          )
        return

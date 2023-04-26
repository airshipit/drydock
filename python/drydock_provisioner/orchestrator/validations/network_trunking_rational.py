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

import drydock_provisioner.objects.fields as hd_fields


class NetworkTrunkingRational(Validators):

    def __init__(self):
        super().__init__('Network Trunking Rationalty', "DD2004")

    def run_validation(self, site_design, orchestrator=None):
        """
        This check ensures that for each NetworkLink if the allowed networks are greater then 1 trunking mode is
        enabled. It also makes sure that if trunking mode is disabled then a default network is defined.
        """
        network_link_list = site_design.network_links or []

        for network_link in network_link_list:
            allowed_networks = network_link.allowed_networks
            # if allowed networks > 1 trunking must be enabled
            if (len(allowed_networks) > 1 and network_link.trunk_mode
                    == hd_fields.NetworkLinkTrunkingMode.Disabled):
                msg = ('If there is more than 1 allowed network,'
                       'trunking mode must be enabled')
                self.report_error(
                    msg, [network_link.doc_ref],
                    "Reduce the allowed network list to 1 or enable trunking on the link."
                )

            # trunking mode is disabled, default_network must be defined
            if (network_link.trunk_mode
                    == hd_fields.NetworkLinkTrunkingMode.Disabled
                    and network_link.native_network is None):

                msg = 'Trunking mode is disabled, a trunking default_network must be defined'
                self.report_error(
                    msg, [network_link.doc_ref],
                    "Non-trunked links must have a native network defined.")
            elif (network_link.trunk_mode
                  == hd_fields.NetworkLinkTrunkingMode.Disabled
                  and network_link.native_network is not None):
                network = site_design.get_network(network_link.native_network)
                if network and network.vlan_id:
                    msg = "Network link native network has a defined VLAN tag."
                    self.report_error(
                        msg, [network.doc_ref, network_link.doc_ref],
                        "Tagged network not allowed on non-trunked network links."
                    )

        return

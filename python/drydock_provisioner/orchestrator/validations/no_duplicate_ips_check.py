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


class NoDuplicateIpsCheck(Validators):
    def __init__(self):
        super().__init__('Duplicated IP Check', "DD2005")

    def run_validation(self, site_design, orchestrator=None):
        """
        Ensures that the same IP is not assigned to multiple baremetal node definitions by checking each new IP against
        the list of known IPs. If the IP is unique no error is thrown and the new IP will be added to the list to be
        checked against in the future.
        """
        found_ips = {}  # Dictionary Format - IP address: BaremetalNode name

        baremetal_nodes_list = site_design.baremetal_nodes or []

        if not baremetal_nodes_list:
            msg = 'No BaremetalNodes Found.'
            self.report_warn(
                msg, [],
                "Site design unlikely complete with no defined baremetal nodes."
            )
        else:
            for node in baremetal_nodes_list:
                addressing_list = node.addressing or []

                for ip_address in addressing_list:
                    address = ip_address.address

                    if address in found_ips and address is not None:
                        msg = ('Duplicate IP Address Found: %s ' % address)
                        self.report_error(
                            msg, [node.doc_ref, found_ips[address].doc_ref],
                            "Select unique IP addresses for each node.")
                    elif address is not None:
                        found_ips[address] = node

        return

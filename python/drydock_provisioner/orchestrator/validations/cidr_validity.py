# Copyright 2019 AT&T Intellectual Property.  All other rights reserved.
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
import ipaddress

from drydock_provisioner.orchestrator.validations.validators import Validators


class CidrValidity(Validators):

    def __init__(self):
        super().__init__('CIDR Validity', 'DD2006')

    def run_validation(self, site_design, orchestrator=None):
        """
        Ensures that the network CIDR provided is acceptable to MAAS which
        means the CIDR should not have host bits set
        """
        network_list = site_design.networks or []

        if not network_list:
            msg = 'No networks found.'
            self.report_warn(
                msg, [],
                'Site design likely incomplete without defined networks')
        else:
            for net in network_list:
                # Verify that the CIDR does not have host bits set
                try:
                    ipaddress.ip_network(net.cidr)
                except ValueError as e:
                    if str(e) == (net.cidr + " has host bits set"):
                        msg = 'The provided CIDR %s has host bits set' % net.cidr
                        valid_cidr = ipaddress.ip_network(net.cidr,
                                                          strict=False)
                        self.report_error(
                            msg, [net.doc_ref],
                            "Provide a CIDR acceptable by MAAS: %s" %
                            str(valid_cidr))
        return

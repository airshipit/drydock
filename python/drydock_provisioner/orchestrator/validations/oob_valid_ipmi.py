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


class IpmiValidity(Validators):
    def __init__(self):
        super().__init__('Valid IPMI Configuration', 'DD4001')

    def run_validation(self, site_design, orchestrator=None):
        """For all IPMI-based nodes, check for a valid configuration.

        1. Check that the node has an IP address assigned on the oob network
        2. Check that credentials are defined
        """
        required_params = ['account', 'credential', 'network']

        baremetal_node_list = site_design.baremetal_nodes or []

        for baremetal_node in baremetal_node_list:
            if baremetal_node.oob_type == 'ipmi':
                for p in required_params:
                    if not baremetal_node.oob_parameters.get(p, None):
                        msg = (
                            'OOB parameter %s for IPMI node %s missing.' % p,
                            baremetal_node.name)
                        self.report_error(msg, [baremetal_node.doc_ref],
                                          "Define OOB parameter %s" % p)
                oob_addr = None
                if baremetal_node.oob_parameters.get('network', None):
                    oob_net = baremetal_node.oob_parameters.get('network')
                    for a in baremetal_node.addressing:
                        if a.network == oob_net:
                            oob_addr = a.address
                if not oob_addr:
                    msg = ('OOB address missing for IPMI node %s.' %
                           baremetal_node.name)
                    self.report_error(
                        msg, [baremetal_node.doc_ref],
                        "Provide address to node OOB interface.")
        return

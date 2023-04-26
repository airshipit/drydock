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


class LibvirtValidity(Validators):

    def __init__(self):
        super().__init__('Valid Libvirt Configuration', 'DD4002')

    def run_validation(self, site_design, orchestrator=None):
        """For all libvirt-based nodes, check for a valid configuration.

        1. Check that the node has a valid libvirt_uri
        2. Check that boot MAC address is defined
        """
        baremetal_node_list = site_design.baremetal_nodes or []

        for baremetal_node in baremetal_node_list:
            if baremetal_node.oob_type == 'libvirt':
                libvirt_uri = baremetal_node.oob_parameters.get(
                    'libvirt_uri', None)
                if not libvirt_uri:
                    msg = ('OOB parameter libvirt_uri missing for node %s.' %
                           baremetal_node.name)
                    self.report_error(
                        msg, [baremetal_node.doc_ref],
                        "Provide libvirt URI to node hypervisor.")
                else:
                    if not libvirt_uri.startswith("qemu+ssh"):
                        msg = 'OOB parameter libvirt_uri has invalid scheme.'
                        self.report_error(
                            msg, [baremetal_node.doc_ref],
                            "Only scheme 'qemu+ssh' is supported.")
                if not baremetal_node.boot_mac:
                    msg = 'libvirt-based node requries defined boot MAC address.'
                    self.report_error(
                        msg, [baremetal_node.doc_ref],
                        "Specify the node's PXE MAC address in metadata.boot_mac"
                    )
        return

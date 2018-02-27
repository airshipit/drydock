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

from drydock_provisioner.objects.task import TaskStatusMessage

class NoDuplicateIpsCheck(Validators):
    def __init__(self):
        super().__init__('No Duplicate IPs Check', 1005)

    def execute(self, site_design, orchestrator=None):
        """
        Ensures that the same IP is not assigned to multiple baremetal node definitions by checking each new IP against
        the list of known IPs. If the IP is unique no error is thrown and the new IP will be added to the list to be
        checked against in the future.
        """
        found_ips = {}  # Dictionary Format - IP address: BaremetalNode name
        message_list = []

        site_design = site_design.obj_to_simple()
        baremetal_nodes_list = site_design.get('baremetal_nodes', [])

        if not baremetal_nodes_list:
            msg = 'No BaremetalNodes Found.'
            message_list.append(
                TaskStatusMessage(
                    msg=msg, error=False, ctx_type='NA', ctx='NA'))
        else:
            for node in baremetal_nodes_list:
                addressing_list = node.get('addressing', [])

                for ip_address in addressing_list:
                    address = ip_address.get('address')
                    node_name = node.get('name')

                    if address in found_ips and address is not None:
                        msg = ('Error! Duplicate IP Address Found: %s '
                               'is in use by both %s and %s.' %
                               (address, found_ips[address], node_name))
                        message_list.append(
                            TaskStatusMessage(
                                msg=msg, error=True, ctx_type='NA', ctx='NA'))
                    elif address is not None:
                        found_ips[address] = node_name

        if not message_list:
            msg = 'No Duplicate IP Addresses.'
            message_list.append(
                TaskStatusMessage(
                    msg=msg, error=False, ctx_type='NA', ctx='NA'))

        return Validators.report_results(self, message_list)

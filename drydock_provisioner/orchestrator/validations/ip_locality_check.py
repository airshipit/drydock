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

from drydock_provisioner.objects.task import TaskStatusMessage

class IpLocalityCheck(Validators):
    def __init__(self):
        super().__init__('IP Locality Check', 1002)

    def execute(self, site_design, orchestrator=None):
        """
        Ensures that each IP addresses assigned to a baremetal node is within the defined CIDR for the network. Also
        verifies that the gateway IP for each static route of a network is within that network's CIDR.
        """
        network_dict = {}  # Dictionary Format - network name: cidr
        message_list = []

        site_design = site_design.obj_to_simple()
        baremetal_nodes_list = site_design.get('baremetal_nodes', [])
        network_list = site_design.get('networks', [])

        if not network_list:
            msg = 'No networks found.'
            message_list.append(
                TaskStatusMessage(
                    msg=msg, error=False, ctx_type='NA', ctx='NA'))
        else:
            for net in network_list:
                name = net.get('name')
                cidr = net.get('cidr')
                routes = net.get('routes', [])

                cidr_range = IPNetwork(cidr)
                network_dict[name] = cidr_range

                if routes:
                    for r in routes:
                        gateway = r.get('gateway')

                        if not gateway:
                            msg = 'No gateway found for route %s.' % routes
                            message_list.append(
                                TaskStatusMessage(
                                    msg=msg,
                                    error=True,
                                    ctx_type='NA',
                                    ctx='NA'))
                        else:
                            ip = IPAddress(gateway)
                            if ip not in cidr_range:
                                msg = (
                                    'IP Locality Error: The gateway IP Address %s '
                                    'is not within the defined CIDR: %s of %s.'
                                    % (gateway, cidr, name))
                                message_list.append(
                                    TaskStatusMessage(
                                        msg=msg,
                                        error=True,
                                        ctx_type='NA',
                                        ctx='NA'))
        if not baremetal_nodes_list:
            msg = 'No baremetal_nodes found.'
            message_list.append(
                TaskStatusMessage(
                    msg=msg, error=False, ctx_type='NA', ctx='NA'))
        else:
            for node in baremetal_nodes_list:
                addressing_list = node.get('addressing', [])

                for ip_address in addressing_list:
                    ip_address_network_name = ip_address.get('network')
                    address = ip_address.get('address')
                    ip_type = ip_address.get('type')

                    if ip_type is not 'dhcp':
                        if ip_address_network_name not in network_dict:
                            msg = 'IP Locality Error: %s is not a valid network.' \
                                  % (ip_address_network_name)
                            message_list.append(
                                TaskStatusMessage(
                                    msg=msg,
                                    error=True,
                                    ctx_type='NA',
                                    ctx='NA'))
                        else:
                            if IPAddress(address) not in IPNetwork(
                                    network_dict[ip_address_network_name]):
                                msg = (
                                    'IP Locality Error: The IP Address %s '
                                    'is not within the defined CIDR: %s of %s .'
                                    % (address,
                                       network_dict[ip_address_network_name],
                                       ip_address_network_name))
                                message_list.append(
                                    TaskStatusMessage(
                                        msg=msg,
                                        error=True,
                                        ctx_type='NA',
                                        ctx='NA'))
        if not message_list:
            msg = 'IP Locality Success'
            message_list.append(
                TaskStatusMessage(
                    msg=msg, error=False, ctx_type='NA', ctx='NA'))

        return Validators.report_results(self, message_list)

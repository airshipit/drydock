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

class MtuRational(Validators):
    def __init__(self):
        super().__init__('MTU Rational', 1003)

    def execute(self, site_design, orchestrator=None):
        """
        Ensure that the MTU for each network is equal or less than the MTU defined
        for the parent NetworkLink for that network.

        Ensure that each defined MTU is a rational size, say > 1400 and < 64000
        """
        message_list = []
        site_design = site_design.obj_to_simple()

        network_links = site_design.get('network_links', [])
        networks = site_design.get('networks', [])

        parent_mtu_check = {}

        for network_link in network_links:
            mtu = network_link.get('mtu')
            # check mtu > 1400 and < 64000
            if mtu and (mtu < 1400 or mtu > 64000):
                msg = 'Mtu Error: Mtu must be between 1400 and 64000; on Network Link %s.' % network_link.get(
                    'name')
                message_list.append(
                    TaskStatusMessage(
                        msg=msg, error=True, ctx_type='NA', ctx='NA'))

            # add assigned network to dict with parent mtu
            assigned_network = network_link.get('native_network')
            parent_mtu_check[assigned_network] = mtu

        for network in networks:
            network_mtu = network.get('mtu')

            # check mtu > 1400 and < 64000
            if network_mtu and (network_mtu < 1400 or network_mtu > 64000):
                msg = 'Mtu Error: Mtu must be between 1400 and 64000; on Network %s.' % network.get(
                    'name')
                message_list.append(
                    TaskStatusMessage(
                        msg=msg, error=True, ctx_type='NA', ctx='NA'))

            name = network.get('name')
            parent_mtu = parent_mtu_check.get(name)
            if network_mtu and parent_mtu:
                # check to make sure mtu for network is <= parent network link
                if network_mtu > parent_mtu:
                    msg = 'Mtu Error: Mtu must be <= the parent Network Link; for Network %s' % (
                        network.get('name'))
                    message_list.append(
                        TaskStatusMessage(
                            msg=msg, error=True, ctx_type='NA', ctx='NA'))

        if not message_list:
            message_list.append(
                TaskStatusMessage(
                    msg='Mtu', error=False, ctx_type='NA', ctx='NA'))

        return Validators.report_results(self, message_list)

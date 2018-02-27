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
from drydock_provisioner.objects.task import TaskStatusMessage

class NetworkTrunkingRational(Validators):
    def __init__(self):
        super().__init__('Network Trunking Rational', 1004)

    def execute(self, site_design, orchestrator=None):
        """
        This check ensures that for each NetworkLink if the allowed networks are greater then 1 trunking mode is
        enabled. It also makes sure that if trunking mode is disabled then a default network is defined.
        """
        message_list = []
        site_design = site_design.obj_to_simple()

        network_link_list = site_design.get('network_links', [])

        for network_link in network_link_list:
            allowed_networks = network_link.get('allowed_networks', [])
            # if allowed networks > 1 trunking must be enabled
            if (len(allowed_networks) > 1 and network_link.get('trunk_mode') ==
                    hd_fields.NetworkLinkTrunkingMode.Disabled):

                msg = (
                    'Rational Network Trunking Error: If there is more than 1 allowed network,'
                    'trunking mode must be enabled; on NetworkLink %s' %
                    network_link.get('name'))

                message_list.append(
                    TaskStatusMessage(
                        msg=msg, error=True, ctx_type='NA', ctx='NA'))

            # trunking mode is disabled, default_network must be defined
            if (network_link.get(
                    'trunk_mode') == hd_fields.NetworkLinkTrunkingMode.Disabled
                    and network_link.get('native_network') is None):

                msg = (
                    'Rational Network Trunking Error: Trunking mode is disabled, a trunking'
                    'default_network must be defined; on NetworkLink %s' %
                    network_link.get('name'))

                message_list.append(
                    TaskStatusMessage(
                        msg=msg, error=True, ctx_type='NA', ctx='NA'))

        if not message_list:
            message_list.append(
                TaskStatusMessage(
                    msg='Rational Network Trunking',
                    error=False,
                    ctx_type='NA',
                    ctx='NA'))

        return Validators.report_results(self, message_list)

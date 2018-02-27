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

class UniqueNetworkCheck(Validators):
    def __init__(self):
        super().__init__('Unique Network Check', 1010)

    def execute(self, site_design, orchestrator=None):
        """
        Ensures that each network name appears at most once between all NetworkLink
        allowed networks
        """
        message_list = []
        site_design = site_design.obj_to_simple()
        network_link_list = site_design.get('network_links', [])
        compare = {}

        for network_link in network_link_list:
            allowed_network_list = network_link.get('allowed_networks', [])
            compare[network_link.get('name')] = allowed_network_list

        # This checks the allowed networks for each network link against
        # the other allowed networks
        checked_pairs = []
        for network_link_name in compare:
            allowed_network_list_1 = compare[network_link_name]

            for network_link_name_2 in compare:
                if (network_link_name is not network_link_name_2
                        and sorted([network_link_name, network_link_name_2
                                    ]) not in checked_pairs):
                    checked_pairs.append(
                        sorted([network_link_name, network_link_name_2]))
                    allowed_network_list_2 = compare[network_link_name_2]
                    # creates a list of duplicated allowed networks
                    duplicated_names = [
                        i for i in allowed_network_list_1
                        if i in allowed_network_list_2
                    ]

                    for name in duplicated_names:
                        msg = (
                            'Unique Network Error: Allowed network %s duplicated on NetworkLink %s and NetworkLink '
                            '%s' % (name, network_link_name,
                                    network_link_name_2))
                        message_list.append(
                            TaskStatusMessage(
                                msg=msg, error=True, ctx_type='NA', ctx='NA'))

        if not message_list:
            message_list.append(
                TaskStatusMessage(
                    msg='Unique Network', error=False, ctx_type='NA',
                    ctx='NA'))

        return Validators.report_results(self, message_list)

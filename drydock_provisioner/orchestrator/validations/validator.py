# Copyright 2017 AT&T Intellectual Property.  All other rights reserved.
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
"""Business Logic Validation"""

import drydock_provisioner.objects.fields as hd_fields

from drydock_provisioner.objects.task import TaskStatus
from drydock_provisioner.objects.task import TaskStatusMessage


class Validator():
    def validate_design(self, site_design, result_status=None):
        """Validate the design in site_design passes all validation rules.

        Apply all validation rules to the design in site_design. If result_status is
        defined, update it with validation messages. Otherwise a new status instance
        will be created and returned.

        :param site_design: instance of objects.SiteDesign
        :param result_status: instance of objects.TaskStatus
        """

        if result_status is None:
            result_status = TaskStatus()

        validation_error = False
        for rule in rule_set:
            output = rule(site_design)
            result_status.message_list.extend(output)
            error_msg = [m for m in output if m.error]
            result_status.error_count = result_status.error_count + len(error_msg)
            if len(error_msg) > 0:
                validation_error = True

        if validation_error:
            result_status.set_status(hd_fields.ValidationResult.Failure)
        else:
            result_status.set_status(hd_fields.ValidationResult.Success)

        return result_status

    @classmethod
    def rational_network_bond(cls, site_design):
        """
        Ensures that NetworkLink 'bonding' is rational
        """
        message_list = []
        site_design = site_design.obj_to_simple()

        network_links = site_design.get('network_links', [])

        for network_link in network_links:
            bonding_mode = network_link.get('bonding_mode', [])

            if bonding_mode == 'disabled':
                # check to make sure nothing else is specified
                if any([network_link.get(x) for x in ['bonding_peer_rate', 'bonding_xmit_hash',
                        'bonding_mon_rate', 'bonding_up_delay', 'bonding_down_delay']]):

                    msg = ('Network Link Bonding Error: If bonding mode is disabled no other bond option can be'
                           'specified; on BaremetalNode %s' % network_link.get('name'))

                    message_list.append(TaskStatusMessage(msg=msg, error=True, ctx_type='NA', ctx='NA'))

            elif bonding_mode == '802.3ad':
                # check if up_delay and down_delay are >= mon_rate
                mon_rate = network_link.get('bonding_mon_rate')
                if network_link.get('bonding_up_delay') < mon_rate:
                    msg = ('Network Link Bonding Error: Up delay is less '
                           'than mon rate on BaremetalNode %s' % (network_link.get('name')))

                    message_list.append(TaskStatusMessage(msg=msg, error=True, ctx_type='NA', ctx='NA'))

                if network_link.get('bonding_down_delay') < mon_rate:
                    msg = ('Network Link Bonding Error: Down delay is '
                           'less than mon rate on BaremetalNode %s' % (network_link.get('name')))

                    message_list.append(TaskStatusMessage(msg=msg, error=True, ctx_type='NA', ctx='NA'))

            elif bonding_mode in ['active-backup', 'balanced-rr']:
                # make sure hash and peer_rate are NOT defined
                if network_link.get('bonding_xmit_hash'):
                    msg = ('Network Link Bonding Error: Hash cannot be defined if bond mode is '
                           '%s, on BaremetalNode %s' % (bonding_mode, network_link.get('name')))

                    message_list.append(TaskStatusMessage(msg=msg, error=True, ctx_type='NA', ctx='NA'))

                if network_link.get('bonding_peer_rate'):
                    msg = ('Network Link Bonding Error: Peer rate cannot be defined if bond mode is '
                           '%s, on BaremetalNode %s' % (bonding_mode, network_link.get('name')))

                    message_list.append(TaskStatusMessage(msg=msg, error=True, ctx_type='NA', ctx='NA'))

        if not message_list:
            message_list.append(TaskStatusMessage(msg='Network Link Bonding', error=False, ctx_type='NA', ctx='NA'))
        return message_list

    @classmethod
    def network_trunking_rational(cls, site_design):
        """
        Ensures that Network Trunking is Rational
        """

        message_list = []
        site_design = site_design.obj_to_simple()

        network_link_list = site_design.get('network_links', [])

        for network_link in network_link_list:
            allowed_networks = network_link.get('allowed_networks', [])
            # if allowed networks > 1 trunking must be enabled
            if (len(allowed_networks) > 1
                    and network_link.get('trunk_mode') == hd_fields.NetworkLinkTrunkingMode.Disabled):

                msg = ('Rational Network Trunking Error: If there is more than 1 allowed network,'
                       'trunking mode must be enabled; on NetworkLink %s' % network_link.get('name'))

                message_list.append(TaskStatusMessage(msg=msg, error=True, ctx_type='NA', ctx='NA'))

            # trunking mode is disabled, default_network must be defined
            if (network_link.get('trunk_mode') == hd_fields.NetworkLinkTrunkingMode.Disabled
                    and network_link.get('native_network') is None):

                msg = ('Rational Network Trunking Error: Trunking mode is disabled, a trunking'
                       'default_network must be defined; on NetworkLink %s' % network_link.get('name'))

                message_list.append(TaskStatusMessage(msg=msg, error=True, ctx_type='NA', ctx='NA'))

        if not message_list:
            message_list.append(
                TaskStatusMessage(msg='Rational Network Trunking', error=False, ctx_type='NA', ctx='NA'))

        return message_list


rule_set = [
    Validator.rational_network_bond,
    Validator.network_trunking_rational,
]

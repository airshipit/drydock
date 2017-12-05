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
                if any([
                        network_link.get(x)
                        for x in [
                            'bonding_peer_rate', 'bonding_xmit_hash', 'bonding_mon_rate', 'bonding_up_delay',
                            'bonding_down_delay'
                        ]
                ]):

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

    @classmethod
    def storage_partitioning(cls, site_design):
        """
        Checks storage partitioning
        """
        message_list = []
        site_design = site_design.obj_to_simple()

        baremetal_nodes = site_design.get('baremetal_nodes', [])

        volume_group_check_list = []

        for baremetal_node in baremetal_nodes:
            storage_devices_list = baremetal_node.get('storage_devices', [])

            for storage_device in storage_devices_list:
                partitions_list = storage_device.get('partitions')
                volume_group = storage_device.get('volume_group')

                # error if both or neither is defined
                if all([partitions_list, volume_group]) or not any([partitions_list, volume_group]):
                    msg = ('Storage Partitioning Error: Either a volume group '
                           'OR partitions must be defined for each storage '
                           'device; on BaremetalNode '
                           '%s' % baremetal_node.get('name'))
                    message_list.append(TaskStatusMessage(msg=msg, error=True, ctx_type='NA', ctx='NA'))

                # if there is a volume group add to list
                if volume_group is not None:
                    volume_group_check_list.append(volume_group)

                if partitions_list is not None:
                    for partition in partitions_list:
                        partition_volume_group = partition.get('volume_group')
                        fstype = partition.get('fstype')

                        # error if both or neither is defined
                        if all([fstype, partition_volume_group]) or not any([fstype, partition_volume_group]):
                            msg = ('Storage Partitioning Error: Either a '
                                   'volume group OR file system must be '
                                   'defined defined in a sigle partition; on '
                                   'BaremetalNode %s' % baremetal_node.get('name'))

                            message_list.append(TaskStatusMessage(msg=msg, error=True, ctx_type='NA', ctx='NA'))

                        # if there is a volume group add to list
                        if partition_volume_group is not None:
                            volume_group_check_list.append(volume_group)

            # checks all volume groups are assigned to a partition or storage device
            # if one exist that wasn't found earlier it is unassigned
            all_volume_groups = baremetal_node.get('volume_groups', [])
            for volume_group in all_volume_groups:
                if volume_group.get('name') not in volume_group_check_list:

                    msg = ('Storage Partitioning Error: A volume group must be '
                           'assigned to a storage device or partition; '
                           'volume group %s ' % volume_group.get('name') + ''
                           'on BaremetalNode %s' % baremetal_node.get('name'))

                    message_list.append(TaskStatusMessage(msg=msg, error=True, ctx_type='NA', ctx='NA'))

        if not message_list:
            message_list.append(TaskStatusMessage(msg='Storage Partitioning', error=False, ctx_type='NA', ctx='NA'))
        return message_list

    @classmethod
    def unique_network_check(cls, site_design):
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

        # This checks the allowed networks for each network link aginst
        # the other allowed networks
        checked_pairs = []
        for network_link_name in compare:
            allowed_network_list_1 = compare[network_link_name]

            for network_link_name_2 in compare:
                if (network_link_name is not network_link_name_2
                        and sorted([network_link_name, network_link_name_2]) not in checked_pairs):
                    checked_pairs.append(sorted([network_link_name, network_link_name_2]))
                    allowed_network_list_2 = compare[network_link_name_2]
                    # creates a list of duplicated allowed networks
                    duplicated_names = [i for i in allowed_network_list_1 if i in allowed_network_list_2]

                    for name in duplicated_names:
                        msg = ('Unique Network Error: Allowed network '
                               '%s duplicated on NetworkLink %s ' % (name, network_link_name) + ''
                               ' and NetworkLink %s' % network_link_name_2)
                        message_list.append(TaskStatusMessage(msg=msg, error=True, ctx_type='NA', ctx='NA'))

        if not message_list:
            message_list.append(TaskStatusMessage(msg='Unique Network', error=False, ctx_type='NA', ctx='NA'))
        return message_list

    @classmethod
    def mtu_rational(cls, site_design):
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
                msg = 'Mtu Error: Mtu must be between 1400 and 64000; on Network Link %s.' % network_link.get('name')
                message_list.append(TaskStatusMessage(msg=msg, error=True, ctx_type='NA', ctx='NA'))

            # add assigned network to dict with parent mtu
            assigned_network = network_link.get('native_network')
            parent_mtu_check[assigned_network] = mtu

        for network in networks:
            network_mtu = network.get('mtu')

            # check mtu > 1400 and < 64000
            if network_mtu and (network_mtu < 1400 or network_mtu > 64000):
                msg = 'Mtu Error: Mtu must be between 1400 and 64000; on Network %s.' % network.get('name')
                message_list.append(TaskStatusMessage(msg=msg, error=True, ctx_type='NA', ctx='NA'))

            name = network.get('name')
            parent_mtu = parent_mtu_check.get(name)
            if network_mtu and parent_mtu:
                # check to make sure mtu for network is <= parent network link
                if network_mtu > parent_mtu:
                    msg = 'Mtu Error: Mtu must be <= the parent Network Link; for Network %s' % (network.get('name'))
                    message_list.append(TaskStatusMessage(msg=msg, error=True, ctx_type='NA', ctx='NA'))

        if not message_list:
            message_list.append(TaskStatusMessage(msg='Mtu', error=False, ctx_type='NA', ctx='NA'))
        return message_list

    @classmethod
    def storage_sizing(cls, site_design):
        """
        Ensures that for a partitioned physical device or logical volumes
        in a volume group, if sizing is a percentage then those percentages
        do not sum > 99% and have no negitive values
        """

        message_list = []
        site_design = site_design.obj_to_simple()

        baremetal_nodes = site_design.get('baremetal_nodes', [])

        for baremetal_node in baremetal_nodes:
            storage_device_list = baremetal_node.get('storage_devices', [])

            for storage_device in storage_device_list:
                partition_list = storage_device.get('partitions', [])
                partition_sum = 0
                for partition in partition_list:
                    size = partition.get('size')
                    percent = size.split('%')
                    if len(percent) == 2:
                        if int(percent[0]) < 0:
                            msg = ('Storage Sizing Error: Storage partition size is < 0 '
                                   'on Baremetal Node %s' % baremetal_node.get('name'))
                            message_list.append(TaskStatusMessage(msg=msg, error=True, ctx_type='NA', ctx='NA'))

                        partition_sum += int(percent[0])

                    if partition_sum > 99:
                        msg = ('Storage Sizing Error: Storage partition size is greater than '
                               '99 on Baremetal Node %s' % baremetal_node.get('name'))
                        message_list.append(TaskStatusMessage(msg=msg, error=True, ctx_type='NA', ctx='NA'))

                volume_groups = baremetal_node.get('volume_groups', [])
                volume_sum = 0
                for volume_group in volume_groups:
                    logical_volume_list = volume_group.get('logical_volumes', [])
                    for logical_volume in logical_volume_list:
                        size = logical_volume.get('size')
                        percent = size.split('%')
                        if len(percent) == 2:
                            if int(percent[0]) < 0:
                                msg = ('Storage Sizing Error: Storage volume size is < 0 '
                                       'on Baremetal Node %s' % baremetal_node.get('name'))
                                message_list.append(TaskStatusMessage(msg=msg, error=True, ctx_type='NA', ctx='NA'))
                            volume_sum += int(percent[0])

                    if volume_sum > 99:
                        msg = ('Storage Sizing Error: Storage volume size is greater '
                               'than 99 on Baremetal Node %s.' % baremetal_node.get('name'))
                        message_list.append(TaskStatusMessage(msg=msg, error=True, ctx_type='NA', ctx='NA'))

        if not message_list:
            message_list.append(TaskStatusMessage(msg='Storage Sizing', error=False, ctx_type='NA', ctx='NA'))
        return message_list


rule_set = [
    Validator.rational_network_bond,
    Validator.network_trunking_rational,
    Validator.storage_partitioning,
    Validator.unique_network_check,
    Validator.mtu_rational,
    Validator.storage_sizing,
]

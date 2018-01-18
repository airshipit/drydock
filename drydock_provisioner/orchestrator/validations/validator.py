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
import drydock_provisioner.error as errors

from netaddr import IPNetwork, IPAddress
from drydock_provisioner.orchestrator.util import SimpleBytes
from drydock_provisioner.objects.task import TaskStatus, TaskStatusMessage


class Validator():
    def __init__(self, orchestrator):
        """Create a validator with a reference to the orchestrator.

        :param orchestrator: instance of Orchestrator
        """
        self.orchestrator = orchestrator

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
            output = rule(site_design, orchestrator=self.orchestrator)
            result_status.message_list.extend(output)
            error_msg = [m for m in output if m.error]
            result_status.error_count = result_status.error_count + len(
                error_msg)
            if len(error_msg) > 0:
                validation_error = True

        if validation_error:
            result_status.set_status(hd_fields.ValidationResult.Failure)
        else:
            result_status.set_status(hd_fields.ValidationResult.Success)

        return result_status

    @classmethod
    def valid_platform_selection(cls, site_design, orchestrator=None):
        """Validate that the platform selection for all nodes is valid.

        Each node specifies an ``image`` and a ``kernel`` to use for
        deployment. Check that these are valid for the image repoistory
        configured in MAAS.
        """
        message_list = list()

        try:
            node_driver = orchestrator.enabled_drivers['node']
        except KeyError:
            message_list.append(
                TaskStatusMessage(
                    msg="Platform Validation: No enabled node driver, image"
                    "and kernel selections not validated.",
                    error=False,
                    ctx_type='NA',
                    ctx='NA'))
            return message_list

        valid_images = node_driver.get_available_images()

        valid_kernels = dict()

        for i in valid_images:
            valid_kernels[i] = node_driver.get_available_kernels(i)

        for n in site_design.baremetal_nodes:
            if n.image in valid_images:
                if n.kernel in valid_kernels[n.image]:
                    continue
                message_list.append(
                    TaskStatusMessage(
                        msg="Platform Validation: invalid kernel %s for node %s."
                        % (n.kernel, n.name),
                        error=True,
                        ctx_type='NA',
                        ctx='NA'))
                continue
            message_list.append(
                TaskStatusMessage(
                    msg="Platform Validation: invalid image %s for node %s." %
                    (n.image, n.name),
                    error=True,
                    ctx_type='NA',
                    ctx='NA'))
        if not message_list:
            message_list.append(
                TaskStatusMessage(
                    msg="Platform Validation: all nodes have valid "
                    "image and kernel selections.",
                    error=False,
                    ctx_type='NA',
                    ctx='NA'))

        return message_list

    @classmethod
    def rational_network_bond(cls, site_design, orchestrator=None):
        """
        This check ensures that each NetworkLink has a rational bonding setup.
        If the bonding mode is set to 'disabled' then it ensures that no other options are specified.
        If the bonding mode it set to '802.3ad' then it ensures that the bonding up delay and the bonding down delay
        are both greater then or equal to the mon rate.
        If the bonding mode is set to active-backup or balanced-rr then it ensures that the bonding hash and the
        bonding peer rate are both NOT defined.
        """
        message_list = []
        site_design = site_design.obj_to_simple()

        network_links = site_design.get('network_links', [])

        for network_link in network_links:
            bonding_mode = network_link.get('bonding_mode', [])

            if bonding_mode == 'disabled':
                # check to make sure nothing else is specified
                if any([
                        network_link.get(x) for x in [
                            'bonding_peer_rate', 'bonding_xmit_hash',
                            'bonding_mon_rate', 'bonding_up_delay',
                            'bonding_down_delay'
                        ]
                ]):

                    msg = (
                        'Network Link Bonding Error: If bonding mode is disabled no other bond option can be'
                        'specified; on BaremetalNode %s' %
                        network_link.get('name'))

                    message_list.append(
                        TaskStatusMessage(
                            msg=msg, error=True, ctx_type='NA', ctx='NA'))

            elif bonding_mode == '802.3ad':
                # check if up_delay and down_delay are >= mon_rate
                mon_rate = network_link.get('bonding_mon_rate')
                if network_link.get('bonding_up_delay') < mon_rate:
                    msg = ('Network Link Bonding Error: Up delay is less '
                           'than mon rate on BaremetalNode %s' %
                           (network_link.get('name')))

                    message_list.append(
                        TaskStatusMessage(
                            msg=msg, error=True, ctx_type='NA', ctx='NA'))

                if network_link.get('bonding_down_delay') < mon_rate:
                    msg = ('Network Link Bonding Error: Down delay is '
                           'less than mon rate on BaremetalNode %s' %
                           (network_link.get('name')))

                    message_list.append(
                        TaskStatusMessage(
                            msg=msg, error=True, ctx_type='NA', ctx='NA'))

            elif bonding_mode in ['active-backup', 'balanced-rr']:
                # make sure hash and peer_rate are NOT defined
                if network_link.get('bonding_xmit_hash'):
                    msg = (
                        'Network Link Bonding Error: Hash cannot be defined if bond mode is '
                        '%s, on BaremetalNode %s' % (bonding_mode,
                                                     network_link.get('name')))

                    message_list.append(
                        TaskStatusMessage(
                            msg=msg, error=True, ctx_type='NA', ctx='NA'))

                if network_link.get('bonding_peer_rate'):
                    msg = (
                        'Network Link Bonding Error: Peer rate cannot be defined if bond mode is '
                        '%s, on BaremetalNode %s' % (bonding_mode,
                                                     network_link.get('name')))

                    message_list.append(
                        TaskStatusMessage(
                            msg=msg, error=True, ctx_type='NA', ctx='NA'))

        if not message_list:
            message_list.append(
                TaskStatusMessage(
                    msg='Network Link Bonding',
                    error=False,
                    ctx_type='NA',
                    ctx='NA'))
        return message_list

    @classmethod
    def network_trunking_rational(cls, site_design, orchestrator=None):
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
        return message_list

    @classmethod
    def storage_partitioning(cls, site_design, orchestrator=None):
        """
        This checks that for each storage device a partition list OR volume group is defined. Also for each partition
        list it ensures that a file system and partition volume group are not defined in the same partition.
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
                if all([partitions_list, volume_group
                        ]) or not any([partitions_list, volume_group]):
                    msg = ('Storage Partitioning Error: Either a volume group '
                           'OR partitions must be defined for each storage '
                           'device; on BaremetalNode '
                           '%s' % baremetal_node.get('name'))
                    message_list.append(
                        TaskStatusMessage(
                            msg=msg, error=True, ctx_type='NA', ctx='NA'))

                # if there is a volume group add to list
                if volume_group is not None:
                    volume_group_check_list.append(volume_group)

                if partitions_list is not None:
                    for partition in partitions_list:
                        partition_volume_group = partition.get('volume_group')
                        fstype = partition.get('fstype')

                        # error if both are defined
                        if all([fstype, partition_volume_group]):
                            msg = (
                                'Storage Partitioning Error: Both a volume group AND file system cannot be '
                                'defined in a sigle partition; on BaremetalNode %s'
                                % baremetal_node.get('name'))

                            message_list.append(
                                TaskStatusMessage(
                                    msg=msg,
                                    error=True,
                                    ctx_type='NA',
                                    ctx='NA'))

                        # if there is a volume group add to list
                        if partition_volume_group is not None:
                            volume_group_check_list.append(volume_group)

            # checks all volume groups are assigned to a partition or storage device
            # if one exist that wasn't found earlier it is unassigned
            all_volume_groups = baremetal_node.get('volume_groups', [])
            for volume_group in all_volume_groups:
                if volume_group.get('name') not in volume_group_check_list:

                    msg = (
                        'Storage Partitioning Error: A volume group must be assigned to a storage device or '
                        'partition; volume group %s on BaremetalNode %s' %
                        (volume_group.get('name'), baremetal_node.get('name')))

                    message_list.append(
                        TaskStatusMessage(
                            msg=msg, error=True, ctx_type='NA', ctx='NA'))

        if not message_list:
            message_list.append(
                TaskStatusMessage(
                    msg='Storage Partitioning',
                    error=False,
                    ctx_type='NA',
                    ctx='NA'))
        return message_list

    @classmethod
    def unique_network_check(cls, site_design, orchestrator=None):
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
        return message_list

    @classmethod
    def mtu_rational(cls, site_design, orchestrator=None):
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
        return message_list

    @classmethod
    def storage_sizing(cls, site_design, orchestrator=None):
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
                            msg = (
                                'Storage Sizing Error: Storage partition size is < 0 '
                                'on Baremetal Node %s' %
                                baremetal_node.get('name'))
                            message_list.append(
                                TaskStatusMessage(
                                    msg=msg,
                                    error=True,
                                    ctx_type='NA',
                                    ctx='NA'))

                        partition_sum += int(percent[0])

                    if partition_sum > 99:
                        msg = (
                            'Storage Sizing Error: Storage partition size is greater than '
                            '99 on Baremetal Node %s' %
                            baremetal_node.get('name'))
                        message_list.append(
                            TaskStatusMessage(
                                msg=msg, error=True, ctx_type='NA', ctx='NA'))

                volume_groups = baremetal_node.get('volume_groups', [])
                volume_sum = 0
                for volume_group in volume_groups:
                    logical_volume_list = volume_group.get(
                        'logical_volumes', [])
                    for logical_volume in logical_volume_list:
                        size = logical_volume.get('size')
                        percent = size.split('%')
                        if len(percent) == 2:
                            if int(percent[0]) < 0:
                                msg = (
                                    'Storage Sizing Error: Storage volume size is < 0 '
                                    'on Baremetal Node %s' %
                                    baremetal_node.get('name'))
                                message_list.append(
                                    TaskStatusMessage(
                                        msg=msg,
                                        error=True,
                                        ctx_type='NA',
                                        ctx='NA'))
                            volume_sum += int(percent[0])

                    if volume_sum > 99:
                        msg = (
                            'Storage Sizing Error: Storage volume size is greater '
                            'than 99 on Baremetal Node %s.' %
                            baremetal_node.get('name'))
                        message_list.append(
                            TaskStatusMessage(
                                msg=msg, error=True, ctx_type='NA', ctx='NA'))

        if not message_list:
            message_list.append(
                TaskStatusMessage(
                    msg='Storage Sizing', error=False, ctx_type='NA',
                    ctx='NA'))
        return message_list

    @classmethod
    def no_duplicate_IPs_check(cls, site_design, orchestrator=None):
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

        return message_list

    @classmethod
    def boot_storage_rational(cls, site_design, orchestrator=None):
        """
        Ensures that root volume is defined and is at least 20GB and that boot volume is at least 1 GB
        """
        message_list = []
        site_design = site_design.obj_to_simple()
        BYTES_IN_GB = SimpleBytes.calulate_bytes('1GB')

        baremetal_node_list = site_design.get('baremetal_nodes', [])

        for baremetal_node in baremetal_node_list:
            storage_devices_list = baremetal_node.get('storage_devices', [])

            root_set = False

            for storage_device in storage_devices_list:
                partitions_list = storage_device.get('partitions', [])

                for host_partition in partitions_list:
                    if host_partition.get('name') == 'root':
                        size = host_partition.get('size')
                        try:
                            cal_size = SimpleBytes.calulate_bytes(size)
                            root_set = True
                            # check if size < 20GB
                            if cal_size < 20 * BYTES_IN_GB:
                                msg = (
                                    'Boot Storage Error: Root volume must be > 20GB on BaremetalNode '
                                    '%s' % baremetal_node.get('name'))
                                message_list.append(
                                    TaskStatusMessage(
                                        msg=msg,
                                        error=True,
                                        ctx_type='NA',
                                        ctx='NA'))
                        except errors.InvalidSizeFormat as e:
                            msg = (
                                'Boot Storage Error: Root volume has an invalid size format on BaremetalNode'
                                '%s.' % baremetal_node.get('name'))
                            message_list.append(
                                TaskStatusMessage(
                                    msg=msg,
                                    error=True,
                                    ctx_type='NA',
                                    ctx='NA'))

                    # check make sure root has been defined and boot volume > 1GB
                    if root_set and host_partition.get('name') == 'boot':
                        size = host_partition.get('size')

                        try:
                            cal_size = SimpleBytes.calulate_bytes(size)
                            # check if size < 1GB
                            if cal_size < BYTES_IN_GB:
                                msg = (
                                    'Boot Storage Error: Boot volume must be > 1GB on BaremetalNode '
                                    '%s' % baremetal_node.get('name'))
                                message_list.append(
                                    TaskStatusMessage(
                                        msg=msg,
                                        error=True,
                                        ctx_type='NA',
                                        ctx='NA'))
                        except errors.InvalidSizeFormat as e:
                            msg = (
                                'Boot Storage Error: Boot volume has an invalid size format on BaremetalNode '
                                '%s.' % baremetal_node.get('name'))
                            message_list.append(
                                TaskStatusMessage(
                                    msg=msg,
                                    error=True,
                                    ctx_type='NA',
                                    ctx='NA'))

            # This must be set
            if not root_set:
                msg = (
                    'Boot Storage Error: Root volume has to be set and must be > 20GB on BaremetalNode '
                    '%s' % baremetal_node.get('name'))
                message_list.append(
                    TaskStatusMessage(
                        msg=msg, error=True, ctx_type='NA', ctx='NA'))

        if not message_list:
            message_list.append(
                TaskStatusMessage(
                    msg='Boot Storage', error=False, ctx_type='NA', ctx='NA'))
        return message_list

    @classmethod
    def ip_locality_check(cls, site_design, orchestrator=None):
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
        return message_list


rule_set = [
    Validator.rational_network_bond,
    Validator.network_trunking_rational,
    Validator.storage_partitioning,
    Validator.unique_network_check,
    Validator.mtu_rational,
    Validator.storage_sizing,
    Validator.ip_locality_check,
    Validator.no_duplicate_IPs_check,
    Validator.boot_storage_rational,
    Validator.valid_platform_selection,
]

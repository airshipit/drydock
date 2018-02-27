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

class StoragePartitioning(Validators):
    def __init__(self):
        super().__init__('Storage Partitioning', 1008)

    def execute(self, site_design, orchestrator=None):
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

        return Validators.report_results(self, message_list)

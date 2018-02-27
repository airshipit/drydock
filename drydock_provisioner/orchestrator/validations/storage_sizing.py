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

class StorageSizing(Validators):
    def __init__(self):
        super().__init__('Storage Sizing', 1009)

    def execute(self, site_design, orchestrator=None):
        """
        Ensures that for a partitioned physical device or logical volumes
        in a volume group, if sizing is a percentage then those percentages
        do not sum > 99% and have no negative values
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

        return Validators.report_results(self, message_list)

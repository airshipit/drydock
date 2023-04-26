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


class StorageSizing(Validators):

    def __init__(self):
        super().__init__('Storage Sizing', 'DD2003')

    def run_validation(self, site_design, orchestrator=None):
        """
        Ensures that for a partitioned physical device or logical volumes
        in a volume group, if sizing is a percentage then those percentages
        do not sum > 99% and have no negative values
        """
        baremetal_nodes = site_design.baremetal_nodes or []

        for baremetal_node in baremetal_nodes:
            storage_device_list = baremetal_node.storage_devices or []

            for storage_device in storage_device_list:
                partition_list = storage_device.partitions or []
                partition_sum = 0
                for partition in partition_list:
                    size = partition.size
                    percent = size.split('%')
                    if len(percent) == 2:
                        if int(percent[0]) < 0:
                            msg = (
                                'Storage partition %s on device %s size is < 0'
                                % (partition.name, storage_device.name))
                            self.report_error(
                                msg, [baremetal_node.doc_ref],
                                "Partition size must be a positive number.")

                        partition_sum += int(percent[0])

                    if partition_sum > 99:
                        msg = (
                            'Cumulative partition sizes on device %s is greater than 99%%.'
                            % (storage_device.name))
                        self.report_error(
                            msg, [baremetal_node.doc_ref],
                            "Percentage-based sizes must sum to less than 100%."
                        )

                volume_groups = baremetal_node.volume_groups or []
                volume_sum = 0
                for volume_group in volume_groups:
                    logical_volume_list = volume_group.logical_volumes or []
                    for logical_volume in logical_volume_list:
                        size = logical_volume.size
                        percent = size.split('%')
                        if len(percent) == 2:
                            if int(percent[0]) < 0:
                                msg = ('Logical Volume %s size is < 0 ' %
                                       (logical_volume.name))
                                self.report_error(msg,
                                                  [baremetal_node.doc_ref], "")
                            volume_sum += int(percent[0])

                    if volume_sum > 99:
                        msg = ('Cumulative logical volume size is greater '
                               'than 99% in volume group %s' %
                               (volume_group.name))
                        self.report_error(
                            msg, [baremetal_node.doc_ref],
                            "Percentage-based sizes must sum to less than 100%."
                        )

        return

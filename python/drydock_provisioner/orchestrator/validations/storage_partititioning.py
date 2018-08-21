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


class StoragePartitioning(Validators):
    def __init__(self):
        super().__init__('Storage Partitioning', "DD2002")

    def run_validation(self, site_design, orchestrator=None):
        """
        This checks that for each storage device a partition list OR volume group is defined. Also for each partition
        list it ensures that a file system and partition volume group are not defined in the same partition.
        """
        baremetal_nodes = site_design.baremetal_nodes or []
        volume_group_check_list = []

        for baremetal_node in baremetal_nodes:
            storage_devices_list = baremetal_node.storage_devices or []

            for storage_device in storage_devices_list:
                partitions_list = storage_device.partitions or []
                volume_group = storage_device.volume_group

                # error if both or neither is defined
                if all([partitions_list, volume_group
                        ]) or not any([partitions_list, volume_group]):
                    msg = (
                        'Either a volume group OR partitions must be defined for each storage '
                        'device.')
                    self.report_error(
                        msg, [baremetal_node.doc_ref],
                        "A storage device must be used for exactly one of a volume group "
                        "physical volume or carved into partitions.")

                # if there is a volume group add to list
                if volume_group is not None:
                    volume_group_check_list.append(volume_group)

                for partition in partitions_list:
                    partition_volume_group = partition.volume_group
                    fstype = partition.fstype

                    # error if both are defined
                    if all([fstype, partition_volume_group]):
                        msg = ('Both a volume group AND file system cannot be '
                               'defined in a single partition')
                        self.report_error(
                            msg, [baremetal_node.doc_ref],
                            "A partition can be used for only one of a volume group "
                            "physical volume or formatted as a filesystem.")

                    # if there is a volume group add to list
                    if partition_volume_group is not None:
                        volume_group_check_list.append(volume_group)

            # checks all volume groups are assigned to a partition or storage device
            # if one exist that wasn't found earlier it is unassigned
            all_volume_groups = baremetal_node.volume_groups or []
            for volume_group in all_volume_groups:
                if volume_group.name not in volume_group_check_list:
                    msg = ('Volume group %s not assigned any physical volumes'
                           % (volume_group.name))
                    self.report_error(
                        msg, [baremetal_node.doc_ref],
                        "Each volume group should be assigned at least one storage device "
                        "or partition as a physical volume.")

        return

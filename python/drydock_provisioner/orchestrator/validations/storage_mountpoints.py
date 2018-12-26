# Copyright 2018, Intracom-Telecom
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

class StorageMountpoints(Validators):
    def __init__(self):
        super().__init__('Storage Mountpoint', "DD2004")

    def run_validation(self, site_design, orchestrator=None):
        """
        Ensures that any partitioned physical device or logical volumes
        in a volume group do not use duplicate mount points.
        """
        baremetal_nodes = site_design.baremetal_nodes or []

        for baremetal_node in baremetal_nodes:
            mountpoint_list = []
            storage_device_list = baremetal_node.storage_devices or []
            for storage_device in storage_device_list:
                # Parsing the partitions and volume group of
                # physical storage devices

                partition_list = storage_device.partitions or []
                device_volume_group = storage_device.volume_group

                for partition in partition_list:
                    # Load the mount point of each partition
                    # to a list

                    mountpoint = partition.mountpoint
                    if mountpoint is None:
                        continue
                    if mountpoint in mountpoint_list:
                        msg = ('Mountpoint "{}" already exists'
                               .format(mountpoint))
                        self.report_error(
                            msg, [baremetal_node.doc_ref],
                            'Please use unique mountpoints.')
                        return
                    else:
                        mountpoint_list.append(mountpoint)

                if device_volume_group:
                    volume_groups = baremetal_node.volume_groups or []
                    for volume_group in volume_groups:
                        if volume_group.name == device_volume_group:
                            logical_volume_list = volume_group.logical_volumes or []
                            for logical_volume in logical_volume_list:
                                # Load the mount point of each logical volume
                                # which belongs to the assigned volume group
                                # to a list

                                mountpoint = logical_volume.mountpoint
                                if mountpoint is None:
                                    continue
                                if mountpoint in mountpoint_list:
                                    msg = ('Mountpoint "{}" already exists'
                                           .format(mountpoint))
                                    self.report_error(
                                        msg, [baremetal_node.doc_ref],
                                        'Please use unique mountpoints.')
                                    return
                                else:
                                    mountpoint_list.append(mountpoint)
        return

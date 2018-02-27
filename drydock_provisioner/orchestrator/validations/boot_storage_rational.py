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

import drydock_provisioner.error as errors
from drydock_provisioner.orchestrator.util import SimpleBytes
from drydock_provisioner.objects.task import TaskStatusMessage

class BootStorageRational(Validators):
    def __init__(self):
        super().__init__('Boot Storage Rational', 1001)

    def execute(self, site_design, orchestrator=None):
        """
        Ensures that root volume is defined and is at least 20GB and that boot volume is at least 1 GB
        """
        message_list = []
        site_design = site_design.obj_to_simple()
        BYTES_IN_GB = SimpleBytes.calculate_bytes('1GB')

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
                            cal_size = SimpleBytes.calculate_bytes(size)
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
                            cal_size = SimpleBytes.calculate_bytes(size)
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

        return Validators.report_results(self, message_list)

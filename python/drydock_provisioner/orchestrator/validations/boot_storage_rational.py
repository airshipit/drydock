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


class BootStorageRational(Validators):

    def __init__(self):
        super().__init__('Rational Boot Storage', 'DD1001')

    def run_validation(self, site_design, orchestrator=None):
        """
        Ensures that root volume is defined and is at least 20GB and that boot volume is at least 1 GB
        """
        BYTES_IN_GB = SimpleBytes.calculate_bytes('1GB')

        baremetal_node_list = site_design.baremetal_nodes or []

        for baremetal_node in baremetal_node_list:
            storage_devices_list = baremetal_node.storage_devices or []

            root_set = False

            for storage_device in storage_devices_list:
                partitions_list = storage_device.partitions or []

                for host_partition in partitions_list:
                    if host_partition.name == 'root':
                        size = host_partition.size
                        try:
                            cal_size = SimpleBytes.calculate_bytes(size)
                            root_set = True
                            # check if size < 20GB
                            if cal_size < 20 * BYTES_IN_GB:
                                msg = (
                                    'Root volume must be > 20GB on BaremetalNode '
                                    '%s' % baremetal_node.name)
                                self.report_error(
                                    msg, [baremetal_node.doc_ref],
                                    "Configure a larger root volume")
                        except errors.InvalidSizeFormat:
                            msg = (
                                'Root volume has an invalid size format on BaremetalNode'
                                '%s.' % baremetal_node.name)
                            self.report_error(
                                msg, [baremetal_node.doc_ref],
                                "Use a valid root volume storage specification."
                            )

                    # check make sure root has been defined and boot volume > 1GB
                    if root_set and host_partition.name == 'boot':
                        size = host_partition.size

                        try:
                            cal_size = SimpleBytes.calculate_bytes(size)
                            # check if size < 1GB
                            if cal_size < BYTES_IN_GB:
                                msg = (
                                    'Boot volume must be > 1GB on BaremetalNode '
                                    '%s' % baremetal_node.name)
                                self.report_error(
                                    msg, [baremetal_node.doc_ref],
                                    "Configure a larger boot volume.")
                        except errors.InvalidSizeFormat:
                            msg = (
                                'Boot volume has an invalid size format on BaremetalNode '
                                '%s.' % baremetal_node.name)
                            self.report_error(
                                msg, [baremetal_node.doc_ref],
                                "Use a valid boot volume storage specification."
                            )
            # This must be set
            if not root_set:
                msg = (
                    'Root volume has to be set and must be > 20GB on BaremetalNode '
                    '%s' % baremetal_node.name)
                self.report_error(
                    msg, [baremetal_node.doc_ref],
                    "All nodes require a defined root volume at least 20GB in size."
                )

        return

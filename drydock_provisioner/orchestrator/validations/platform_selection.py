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

class PlatformSelection(Validators):
    def __init__(self):
        super().__init__('Platform Selection', 1006)

    def execute(self, site_design, orchestrator=None):
        """Validate that the platform selection for all nodes is valid.

        Each node specifies an ``image`` and a ``kernel`` to use for
        deployment. Check that these are valid for the image repository
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
            return Validators.report_results(self, message_list)

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

        return Validators.report_results(self, message_list)

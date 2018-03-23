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


class PlatformSelection(Validators):
    def __init__(self):
        super().__init__('Platform Selection', 'DD3001')

    def run_validation(self, site_design, orchestrator=None):
        """Validate that the platform selection for all nodes is valid.

        Each node specifies an ``image`` and a ``kernel`` to use for
        deployment. Check that these are valid for the image repository
        configured in MAAS.
        """
        try:
            node_driver = orchestrator.enabled_drivers['node']
        except KeyError:
            msg = ("Platform Validation: No enabled node driver, image"
                   "and kernel selections not validated.")
            self.report_warn(
                msg, [],
                "Cannot validate platform selection without accessing the node provisioner."
            )
            return

        valid_images = node_driver.get_available_images()

        valid_kernels = dict()

        for i in valid_images:
            valid_kernels[i] = node_driver.get_available_kernels(i)

        node_list = site_design.baremetal_nodes or []

        for n in node_list:
            if n.image in valid_images:
                if n.kernel in valid_kernels[n.image]:
                    continue
                msg = "Platform Validation: invalid kernel %s" % (n.kernel)
                self.report_error(msg, [n.doc_ref],
                                  "Select a valid kernel from: %s" % ",".join(
                                      valid_kernels[n.image]))
                continue
            msg = "Platform Validation: invalid image %s" % (n.image)
            self.report_error(
                msg, [n.doc_ref],
                "Select a valid image from: %s" % ",".join(valid_images))

        return

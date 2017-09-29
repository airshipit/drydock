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
"""Generic OOB driver."""

import drydock_provisioner.objects.fields as hd_fields

from drydock_provisioner.drivers.driver import ProviderDriver


class OobDriver(ProviderDriver):
    """Genneric driver for OOB actions."""

    oob_types_supported = ['']

    def __init__(self, **kwargs):
        super(OobDriver, self).__init__(**kwargs)

        self.supported_actions = [
            hd_fields.OrchestratorAction.ValidateOobServices,
            hd_fields.OrchestratorAction.ConfigNodePxe,
            hd_fields.OrchestratorAction.SetNodeBoot,
            hd_fields.OrchestratorAction.PowerOffNode,
            hd_fields.OrchestratorAction.PowerOnNode,
            hd_fields.OrchestratorAction.PowerCycleNode,
            hd_fields.OrchestratorAction.InterrogateOob
        ]

        self.driver_name = "oob_generic"
        self.driver_key = "oob_generic"
        self.driver_desc = "Generic OOB Driver"

    @classmethod
    def oob_type_support(cls, type_string):
        """Check if this driver support a particular OOB type.

        :param type_string: OOB type to check
        """
        if type_string in cls.oob_types_supported:
            return True

        return False

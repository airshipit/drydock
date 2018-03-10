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

import logging

from drydock_provisioner.statemgmt.state import DrydockState
from drydock_provisioner.orchestrator.orchestrator import Orchestrator

LOG = logging.getLogger(__name__)


class TestKernelParameterReferences(object):
    def test_valid_param_reference(self, deckhand_ingester, input_files,
                                   setup):
        input_file = input_files.join("deckhand_fullsite.yaml")

        design_state = DrydockState()
        design_ref = "file://%s" % str(input_file)

        orchestrator = Orchestrator(
            state_manager=design_state, ingester=deckhand_ingester)

        design_status, design_data = orchestrator.get_effective_site(
            design_ref)

        assert len(design_data.baremetal_nodes) == 2

        node = design_data.get_baremetal_node("compute01")

        assert node.hardware_profile == 'HPGen9v3'

        isolcpu = node.kernel_params.get('isolcpus', None)

        # '2,4' is defined in the HardwareProfile as cpu_sets.sriov
        assert isolcpu == '2,4'

        hugepagesz = node.kernel_params.get('hugepagesz', None)

        assert hugepagesz == '1G'

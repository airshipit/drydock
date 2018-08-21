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

from drydock_provisioner.ingester.ingester import Ingester
from drydock_provisioner.statemgmt.state import DrydockState
from drydock_provisioner.orchestrator.orchestrator import Orchestrator


class TestClass(object):
    def test_design_inheritance(self, input_files, setup):
        input_file = input_files.join("fullsite.yaml")

        design_state = DrydockState()
        design_ref = "file://%s" % str(input_file)

        ingester = Ingester()
        ingester.enable_plugin(
            'drydock_provisioner.ingester.plugins.yaml.YamlIngester')

        orchestrator = Orchestrator(
            state_manager=design_state, ingester=ingester)

        design_status, design_data = orchestrator.get_effective_site(
            design_ref)

        assert len(design_data.baremetal_nodes) == 2

        node = design_data.get_baremetal_node("controller01")

        assert node.hardware_profile == 'HPGen9v3'

        iface = node.get_applied_interface('bond0')

        assert len(iface.get_hw_slaves()) == 2

        iface = node.get_applied_interface('pxe')

        assert len(iface.get_hw_slaves()) == 1

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
"""Test build data collection and persistence."""
import bson

from drydock_provisioner import objects
from drydock_provisioner.drivers.node.maasdriver.actions.node import ConfigureHardware


class TestBuildDataCollection(object):

    def test_build_data_collection(self, setup, blank_state, mocker,
                                   deckhand_orchestrator):
        """Test that the build data collection from MaaS works."""
        sample_data = {
            'lshw': '<xml><test>foo</test></xml>'.encode(),
            'lldp': '<xml><test>bar</test></xml>'.encode(),
        }
        bson_data = bson.BSON.encode(sample_data)

        machine = mocker.MagicMock()
        mocker_config = {
            'get_details.return_value': bson.BSON.decode(bson_data),
            'hostname': 'foo',
        }
        machine.configure_mock(**mocker_config)

        task = objects.Task(statemgr=blank_state)

        action = ConfigureHardware(task, deckhand_orchestrator, blank_state)

        action.collect_build_data(machine)

        bd = blank_state.get_build_data(node_name='foo')

        assert len(bd) == 2

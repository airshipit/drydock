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
"""Test build data collection and persistence."""
from drydock_provisioner.objects import fields as hd_fields
from drydock_provisioner.drivers.node.maasdriver.actions.node import BaseMaasAction
from drydock_provisioner.drivers.node.maasdriver.models.machine import Machine


class TestNodeResultLinks(object):
    def test_create_detail_log_links(self, setup, blank_state, mocker,
                                     input_files, deckhand_orchestrator):
        """Test that the detail log collection from MaaS works."""

        class MockedResponse():

            status_code = 200

            def json(self):
                resp_content = [{
                    "id":
                    3,
                    "data":
                    "SGVsbG8gV29ybGQh",
                    "result_type":
                    0,
                    "script_result":
                    0,
                    "resource_uri":
                    "/MAAS/api/2.0/commissioning-scripts/",
                    "updated":
                    "2018-07-06T14:32:20.129",
                    "node": {
                        "system_id": "r7mqnw"
                    },
                    "created":
                    "2018-07-06T14:37:12.632",
                    "name":
                    "hello_world"
                }]

                return resp_content

        input_file = input_files.join("deckhand_fullsite.yaml")
        design_ref = "file://%s" % str(input_file)

        task = deckhand_orchestrator.create_task(
            action=hd_fields.OrchestratorAction.Noop, design_ref=design_ref)
        task.set_status(hd_fields.TaskStatus.Running)
        task.save()

        api_client = mocker.MagicMock()
        api_client.get.return_value = MockedResponse()

        machine = Machine(api_client)
        machine.resource_id = 'r7mqnw'
        node = mocker.MagicMock()
        node.configure_mock(name='n1')

        action = BaseMaasAction(task, deckhand_orchestrator, blank_state)

        with mocker.patch(
                'drydock_provisioner.drivers.node.maasdriver.actions.node.get_internal_api_href',
                mocker.MagicMock(return_value='http://drydock/api/v1.0')):
            action._add_detail_logs(node, machine, 'hello_world')

        bd = blank_state.get_build_data(task_id=task.task_id)
        assert len(bd) == 1

        links_list = task.result.get_links()

        assert len(links_list) > 0

        for link in links_list:
            assert str(task.task_id) in link

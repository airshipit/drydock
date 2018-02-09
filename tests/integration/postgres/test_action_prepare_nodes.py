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
"""Generic testing for the orchestrator."""
import drydock_provisioner.orchestrator.orchestrator as orch
import drydock_provisioner.objects.fields as hd_fields

from drydock_provisioner.orchestrator.actions.orchestrator import PrepareNodes


class TestActionPrepareNodes(object):
    def test_preparenodes(self, mocker, input_files, deckhand_ingester, setup,
                          drydock_state):
        mock_images = mocker.patch("drydock_provisioner.drivers.node.driver.NodeDriver"
                                   ".get_available_images")
        mock_images.return_value = ['xenial']
        mock_kernels = mocker.patch("drydock_provisioner.drivers.node.driver.NodeDriver"
                                    ".get_available_kernels")
        mock_kernels.return_value = ['ga-16.04', 'hwe-16.04']

        input_file = input_files.join("deckhand_fullsite.yaml")

        design_ref = "file://%s" % str(input_file)

        # Build a dummy object that looks like an oslo_config object
        # so the orchestrator is configured w/ Noop drivers
        class DummyConf(object):
            oob_driver = ['drydock_provisioner.drivers.oob.driver.OobDriver']
            node_driver = 'drydock_provisioner.drivers.node.driver.NodeDriver'
            network_driver = None

        orchestrator = orch.Orchestrator(
            enabled_drivers=DummyConf(),
            state_manager=drydock_state,
            ingester=deckhand_ingester)

        task = orchestrator.create_task(
            design_ref=design_ref,
            action=hd_fields.OrchestratorAction.PrepareNodes)

        action = PrepareNodes(task, orchestrator, drydock_state)
        action.start()

        task = drydock_state.get_task(task.get_id())

        assert task.result.status == hd_fields.ActionResult.Success

        # check that the PrepareNodes action was split
        # with 2 nodes in the definition
        assert len(task.subtask_id_list) == 2

        for st_id in task.subtask_id_list:
            st = drydock_state.get_task(st_id)
            assert st.action == hd_fields.OrchestratorAction.PrepareNodes

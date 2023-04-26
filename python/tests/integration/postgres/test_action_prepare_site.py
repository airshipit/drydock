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

from drydock_provisioner.orchestrator.actions.orchestrator import PrepareSite


class TestActionPrepareSite(object):

    def test_preparesite(self, input_files, deckhand_ingester, setup,
                         drydock_state):
        input_file = input_files.join("deckhand_fullsite.yaml")

        design_ref = "file://%s" % str(input_file)

        # Build a dummy object that looks like an oslo_config object
        # so the orchestrator is configured w/ Noop drivers
        class DummyConf(object):
            oob_driver = list()
            node_driver = 'drydock_provisioner.drivers.node.driver.NodeDriver'
            kubernetes_driver = 'drydock_provisioner.drivers.kubernetes.driver.KubernetesDriver'
            network_driver = None

        orchestrator = orch.Orchestrator(enabled_drivers=DummyConf(),
                                         state_manager=drydock_state,
                                         ingester=deckhand_ingester)

        task = orchestrator.create_task(
            design_ref=design_ref,
            action=hd_fields.OrchestratorAction.PrepareSite)

        action = PrepareSite(task, orchestrator, drydock_state)
        action.start()

        task = drydock_state.get_task(task.get_id())

        assert task.result.status == hd_fields.ActionResult.Success

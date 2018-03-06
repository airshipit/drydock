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
import threading
import time

import drydock_provisioner.orchestrator.orchestrator as orch
import drydock_provisioner.objects.fields as hd_fields


class TestClass(object):
    def test_task_complete(self, deckhand_ingester, input_files, setup,
                           blank_state, mock_get_build_data):
        input_file = input_files.join("deckhand_fullsite.yaml")
        design_ref = "file://%s" % str(input_file)

        orchestrator = orch.Orchestrator(
            state_manager=blank_state, ingester=deckhand_ingester)
        orch_task = orchestrator.create_task(
            action=hd_fields.OrchestratorAction.Noop, design_ref=design_ref)
        orch_task.set_status(hd_fields.TaskStatus.Queued)
        orch_task.save()

        orch_thread = threading.Thread(target=orchestrator.watch_for_tasks)
        orch_thread.start()

        try:
            time.sleep(10)

            orch_task = blank_state.get_task(orch_task.get_id())

            assert orch_task.get_status() == hd_fields.TaskStatus.Complete
        finally:
            orchestrator.stop_orchestrator()
            orch_thread.join(10)

    def test_task_termination(self, input_files, deckhand_ingester, setup,
                              blank_state):
        input_file = input_files.join("deckhand_fullsite.yaml")
        design_ref = "file://%s" % str(input_file)

        orchestrator = orch.Orchestrator(
            state_manager=blank_state, ingester=deckhand_ingester)
        orch_task = orchestrator.create_task(
            action=hd_fields.OrchestratorAction.Noop, design_ref=design_ref)

        orch_task.set_status(hd_fields.TaskStatus.Queued)
        orch_task.save()

        orch_thread = threading.Thread(target=orchestrator.watch_for_tasks)
        orch_thread.start()

        try:
            time.sleep(2)
            orchestrator.terminate_task(orch_task)

            time.sleep(10)
            orch_task = blank_state.get_task(orch_task.get_id())
            assert orch_task.get_status() == hd_fields.TaskStatus.Terminated
        finally:
            orchestrator.stop_orchestrator()
            orch_thread.join(10)

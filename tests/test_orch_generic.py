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

#
# Generic testing for the orchestrator
#

import helm_drydock.orchestrator as orch
import helm_drydock.enum as enum
import helm_drydock.statemgmt as statemgmt
import helm_drydock.model.task as task
import helm_drydock.drivers as drivers
import threading
import time

class TestClass(object):

    def test_driver_threading(self):
        state_mgr = statemgmt.DesignState()
        orchestrator = orch.Orchestrator(state_manager=state_mgr)
        orch_task = task.OrchestratorTask(action=enum.OrchestratorAction.Noop,
                                site="default")

        orchestrator.execute_task(orch_task)

        # Check that each subtask executed in a different thread than this one
        for t in orch_task.subtasks:
            if isinstance(t, drivers.DriverTask):
                assert t.get_manager() != threading.current_thread().name

    def test_task_termination(self):
        state_mgr = statemgmt.DesignState()
        orchestrator = orch.Orchestrator(state_manager=state_mgr)
        orch_task = task.OrchestratorTask(action=enum.OrchestratorAction.Noop,
                                          site="default")

        orch_thread = threading.Thread(target=orchestrator.execute_task,
                                       args=(orch_task,))
        orch_thread.start()

        time.sleep(1)
        orch_task.terminate_task()

        while orch_thread.is_alive():
            time.sleep(1)

        assert orch_task.get_status() == enum.TaskStatus.Terminated

        for t in orch_task.subtasks:
            assert t.get_status() == enum.TaskStatus.Terminated
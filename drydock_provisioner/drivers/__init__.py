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
from threading import Thread, Lock
import uuid
import time

import drydock_provisioner.objects.fields as hd_fields
import drydock_provisioner.statemgmt as statemgmt
import drydock_provisioner.objects.task as tasks
import drydock_provisioner.error as errors

# This is the interface for the orchestrator to access a driver
# TODO Need to have each driver spin up a seperate thread to manage
# driver tasks and feed them via queue
class ProviderDriver(object):

    driver_name = "generic"
    driver_key = "generic"
    driver_desc = "Generic Provider Driver"

    def __init__(self, orchestrator=None, state_manager=None, **kwargs):
        if orchestrator is None:
            raise ValueError("ProviderDriver requires valid orchestrator")

        self.orchestrator = orchestrator

        if state_manager is None:
            raise ValueError("ProviderDriver requires valid state manager")

        self.state_manager = state_manager

        # These are the actions that this driver supports
        self.supported_actions = [hd_fields.OrchestratorAction.Noop]



    def execute_task(self, task_id):
        task = self.state_manager.get_task(task_id)
        task_action = task.action

        if task_action in self.supported_actions:
            task_runner = DriverTaskRunner(task_id, self.state_manager,
                                         self.orchestrator)
            task_runner.start()
        
            while task_runner.is_alive():
                time.sleep(1)

            return
        else:
            raise errors.DriverError("Unsupported action %s for driver %s" % 
                (task_action, self.driver_desc))

# Execute a single task in a separate thread
class DriverTaskRunner(Thread):

    def __init__(self, task_id, state_manager=None, orchestrator=None):
        super(DriverTaskRunner, self).__init__()

        self.orchestrator = orchestrator

        if isinstance(state_manager, statemgmt.DesignState):
            self.state_manager = state_manager
        else:
            raise DriverError("Invalid state manager specified")

        self.task = self.state_manager.get_task(task_id)

        return

    def run(self):
        self.execute_task()

    def execute_task(self):
        if self.task.action == hd_fields.OrchestratorAction.Noop:
            self.orchestrator.task_field_update(self.task.get_id(),
                                                status=hd_fields.TaskStatus.Running)

            i = 0
            while i < 5:
                self.task = self.state_manager.get_task(self.task.get_id())
                i = i + 1
                if self.task.terminate:
                    self.orchestrator.task_field_update(self.task.get_id(),
                                        status=hd_fields.TaskStatus.Terminated)
                    return
                else:
                    time.sleep(1)
                    
            self.orchestrator.task_field_update(self.task.get_id(),
                                    status=hd_fields.TaskStatus.Complete)
            return


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

import helm_drydock.statemgmt as statemgmt
import helm_drydock.enum as  enum
import helm_drydock.model.task as tasks

# This is the interface for the orchestrator to access a driver
# TODO Need to have each driver spin up a seperate thread to manage
# driver tasks and feed them via queue
class ProviderDriver(object):

    def __init__(self, state_manager, orchestrator):
        self.orchestrator = orchestrator
        self.state_manager = state_manager

    def execute_task(self, task_id):
        task_manager = DriverTaskManager(task_id, self.state_manager,
                                         self.orchestrator)
        task_manager.start()
        
        while task_manager.is_alive():
            time.sleep(1)

        return

# Execute a single task in a separate thread
class DriverTaskManager(Thread):

    def __init__(self, task_id, state_manager, orchestrator):
        super(DriverTaskManager, self).__init__()

        self.orchestrator = orchestrator

        if isinstance(state_manager, statemgmt.DesignState):
            self.state_manager = state_manager
        else:
            raise DriverError("Invalid state manager specified")

        self.task = self.state_manager.get_task(task_id)

        return

    def run(self):
        if self.task.target_action == enum.OrchestratorAction.Noop:
            self.orchestrator.task_field_update(self.task.get_id(),
                                                status=enum.TaskStatus.Running)

            i = 0
            while i < 5:
                self.task = self.state_manager.get_task(self.task.get_id())
                i = i + 1
                if self.task.terminate:
                    self.orchestrator.task_field_update(self.task.get_id(),
                                        status=enum.TaskStatus.Terminated)
                    return
                else:
                    time.sleep(1)
                    
            self.orchestrator.task_field_update(self.task.get_id(),
                                    status=enum.TaskStatus.Complete)
            return
        else:
            raise DriverError("Unknown Task action")



class DriverTask(tasks.Task):
    # subclasses implemented by each driver should override this with the list
    # of actions that driver supports

    supported_actions = [enum.OrchestratorAction.Noop]

    def __init__(self, target_design_id=None,
                 target_action=None, task_scope={}, **kwargs):
        super(DriverTask, self).__init__(**kwargs)
        
        if target_design_id is None:
            raise DriverError("target_design_id cannot be None")

        self.target_design_id = target_design_id

        if target_action in self.supported_actions:
            self.target_action = target_action
        else:
            raise DriverError("DriverTask does not support action %s"
                % (target_action))

        self.task_scope = task_scope
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

    def __init__(self, state_manager):
        self.state_manager = state_manager

    def execute_task(self, task):
        task_manager = DriverTaskManager(task, self.state_manager)
        task_manager.start()
        
        while task_manager.is_alive():
            self.state_manager.put_task(task)
            time.sleep(1)

        return

# Execute a single task in a separate thread
class DriverTaskManager(Thread):

    def __init__(self, task, state_manager):
        super(DriverTaskManager, self).__init__()

        if isinstance(task, DriverTask):
            self.task = task
        else:
            raise DriverError("DriverTaskManager must be initialized" \
                "with a DriverTask instance")

        if isinstance(state_manager, statemgmt.DesignState):
            self.state_manager = state_manager
        else:
            raise DriverError("Invalid state manager specified")

        return

    def run():
        self.task.set_manager(self.name)

        if self.task.action == enum.OrchestratorAction.Noop:
            task.set_status(enum.TaskStatus.Running)
            self.state_manager.put_task(task)
            i = 0
            while i < 5:
                i = i + 1
                if task.terminate:
                    task.set_status(enum.TaskStatus.Terminated)
                    self.state_manager.put_task(task)
                    return
                else:
                    time.sleep(1)
            task.set_status(enum.TaskStatus.Complete)
            self.state_manager.put_task(task)
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

        # The DriverTaskManager thread that is managing this task. We
        # don't want a task to be submitted multiple times

        self.task_manager = None

    def set_manager(self, manager_name):
        my_lock = self.get_lock()
        if my_lock:
            if self.task_manager is None:
                self.task_manager = manager_name
            else:
                self.release_lock()
                raise DriverError("Task %s already managed by %s" 
                    % (self.taskid, self.task_manager))
            self.release_lock()
            return True
        raise DriverError("Could not acquire lock")

    def get_manager(self):
        return self.task_manager
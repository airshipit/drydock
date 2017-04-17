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
import uuid
import time
import threading

from enum import Enum, unique

import helm_drydock.drivers as drivers
import helm_drydock.model.task as tasks
import helm_drydock.error as errors

from helm_drydock.enum import TaskStatus, OrchestratorAction

class Orchestrator(object):

    # enabled_drivers is a map which provider drivers
    # should be enabled for use by this orchestrator
    def __init__(self, enabled_drivers=None, state_manager=None):
        self.enabled_drivers = {}

        if enabled_drivers is not None:
            self.enabled_drivers['oob'] = enabled_drivers.get('oob', None)
            self.enabled_drivers['server'] = enabled_drivers.get(
                                                'server', None)
            self.enabled_drivers['network'] = enabled_drivers.get(
                                                'network', None)

        self.state_manager = state_manager


    """
    execute_task

    This is the core of the orchestrator. The task will describe the action
    to take and the context/scope of the command. We will then source
    the current designed state and current built state from the statemgmt
    module. Based on those 3 inputs, we'll decide what is needed next.
    """
    def execute_task(self, task_id):
        if self.state_manager is None:
            raise errors.OrchestratorError("Cannot execute task without" \
                                           " initialized state manager")

        task = self.state_manager.get_task(task_id)

        if task is None:
            raise errors.OrchestratorError("Task %s not found." 
                                            % (task_id))
        # Just for testing now, need to implement with enabled_drivers
        # logic
        if task.action == OrchestratorAction.Noop:
            self.task_field_update(task_id,
                                   status=TaskStatus.Running)        

            driver_task = self.create_task(drivers.DriverTask,
                            target_design_id=0,
                            target_action=OrchestratorAction.Noop,
                            parent_task_id=task.get_id())



            driver = drivers.ProviderDriver(self.state_manager, self)
            driver.execute_task(driver_task.get_id())
            driver_task = self.state_manager.get_task(driver_task.get_id())

            self.task_field_update(task_id, status=driver_task.get_status())
            
            return
        else:
            raise errors.OrchestratorError("Action %s not supported"
                                     % (task.action))

    """
    terminate_task

    Mark a task for termination and optionally propagate the termination
    recursively to all subtasks
    """
    def terminate_task(self, task_id, propagate=True):
        task = self.state_manager.get_task(task_id)

        if task is None:
            raise errors.OrchestratorError("Could find task %s" % task_id)
        else:
            # Terminate initial task first to prevent add'l subtasks

            self.task_field_update(task_id, terminate=True)

            if propagate:
                # Get subtasks list
                subtasks = task.get_subtasks()
    
                for st in subtasks:
                    self.terminate_task(st, propagate=True)
            else:
                return True

    def create_task(self, task_class, **kwargs):
        parent_task_id = kwargs.get('parent_task_id', None)
        new_task = task_class(**kwargs)
        self.state_manager.post_task(new_task)

        if parent_task_id is not None:
            self.task_subtask_add(parent_task_id, new_task.get_id())

        return new_task

    # Lock a task and make all field updates, then unlock it
    def task_field_update(self, task_id, **kwargs):
        lock_id = self.state_manager.lock_task(task_id)
        if lock_id is not None:
            task = self.state_manager.get_task(task_id)
        
            for k,v in kwargs.items():
                print("Setting task %s field %s to %s" % (task_id, k, v))
                setattr(task, k, v)

            self.state_manager.put_task(task, lock_id=lock_id)
            self.state_manager.unlock_task(task_id, lock_id)
            return True
        else:
            return False

    def task_subtask_add(self, task_id, subtask_id):
        lock_id = self.state_manager.lock_task(task_id)
        if lock_id is not None:
            task = self.state_manager.get_task(task_id)
            task.register_subtask(subtask_id)
            self.state_manager.put_task(task, lock_id=lock_id)
            self.state_manager.unlock_task(task_id, lock_id)
            return True
        else:
            return False
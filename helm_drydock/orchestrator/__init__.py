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

        self.thread_objs = {}

    """
    execute_task

    This is the core of the orchestrator. The task will describe the action
    to take and the context/scope of the command. We will then source
    the current designed state and current built state from the statemgmt
    module. Based on those 3 inputs, we'll decide what is needed next.
    """
    def execute_task(self, task):
        if self.state_manager is None:
            raise errors.OrchestratorError("Cannot execute task without" \
                                           " initialized state manager")

        # Just for testing now, need to implement with enabled_drivers
        # logic
        if task.action == OrchestratorAction.Noop:
            task.set_status(TaskStatus.Running)
            self.state_manager.put_task(task)

            driver_task = task.create_subtask(drivers.DriverTask,
                            target_design_id=0,
                            target_action=OrchestratorAction.Noop)
            self.state_manager.post_task(driver_task)

            driver = drivers.ProviderDriver(self.state_manager)
            driver.execute_task(driver_task)

            task.set_status(driver_task.get_status())
            self.state_manager.put_task(task)

            return
        else:
            raise errors.OrchestratorError("Action %s not supported"
                                     % (task.action))
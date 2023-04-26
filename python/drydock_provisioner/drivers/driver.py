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
"""Abstract classes for use by implemented drivers."""

from threading import Thread
import time

import drydock_provisioner.objects.fields as hd_fields
import drydock_provisioner.error as errors

from drydock_provisioner.orchestrator.actions.orchestrator import Noop


class ProviderDriver(object):
    """Generic driver for executing driver actions."""

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
            # Just use the Noop action
            task_action = Noop(task, self.orchestrator, self.state_manager)
            task_runner = DriverActionRunner(task_action)
            task_runner.start()

            while task_runner.is_alive():
                time.sleep(1)

            return
        else:
            raise errors.DriverError("Unsupported action %s for driver %s" %
                                     (task_action, self.driver_desc))


# Execute a single task in a separate thread
class DriverActionRunner(Thread):

    def __init__(self, action=None):
        super().__init__()

        self.action = action
        self.orchestrator = action.orchestrator
        self.state_manager = action.state_manager

    def run(self):
        self.run_action()

    def run_action(self):
        """Run self.action.start() in this thread."""
        if self.action is None:
            raise errors.NoActionDefined(
                "Runner started without a defined action.")

        self.action.start()

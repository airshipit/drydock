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
from enum import Enum, unique

import uuid

class Orchestrator(object):

    # enabled_drivers is a map which provider drivers
    # should be enabled for use by this orchestrator

    def __init__(self, enabled_drivers=None, design_state=None):
        self.enabled_drivers = {}

        self.enabled_drivers['oob'] = enabled_drivers.get('oob', None)
        self.enabled_drivers['server'] = enabled_drivers.get('server', None)
        self.enabled_drivers['network'] = enabled_drivers.get('network', None)

        self.design_state = design_state

    """
    execute_task

    This is the core of the orchestrator. The task will describe the action
    to take and the context/scope of the command. We will then source
    the current designed state and current built state from the statemgmt
    module. Based on those 3 inputs, we'll decide what is needed next.
    """
    def execute_task(self, task):
        if design_state is None:
            raise Exception("Cannot execute task without initialized state manager")


class OrchestrationTask(object):

    def __init__(self, action, **kwargs):
        self.taskid = uuid.uuid4()

        self.action = action

        parent_task = kwargs.get('parent_task','')

        # Validate parameters based on action
        self.site = kwargs.get('site', '')


        if self.site == '':
            raise ValueError("Task requires 'site' parameter")

        if action in [Action.VerifyNode, Action.PrepareNode,
            Action.DeployNode, Action.DestroyNode]:
            self.node_filter = kwargs.get('node_filter', None)

    def child_task(self, action, **kwargs):
        child_task = OrchestrationTask(action, parent_task=self.taskid, site=self.site, **kwargs)
        return child_task





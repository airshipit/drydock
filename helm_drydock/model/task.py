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

from threading import Lock

import helm_drydock.error as errors

from helm_drydock.enum import TaskStatus, OrchestratorAction

class Task(object):

    def __init__(self, **kwargs):
        self.task_id = uuid.uuid4()
        self.status = TaskStatus.Created
        self.terminate = False
        self.subtasks = []
        self.lock_id = None

        self.parent_task_id = kwargs.get('parent_task_id','')

    def get_id(self):
        return self.task_id

    def terminate_task(self):
        self.terminate = True

    def set_status(self, status):
        self.status = status

    def get_status(self):
        return self.status

    def register_subtask(self, subtask_id):
        if self.terminate:
            raise errors.OrchestratorError("Cannot add subtask for parent" \
                                           " marked for termination")
        self.subtasks.append(subtask_id)

    def get_subtasks(self):
        return self.subtasks

class OrchestratorTask(Task):

    def __init__(self, **kwargs):
        super(OrchestratorTask, self).__init__(**kwargs)

        self.action = kwargs.get('action', OrchestratorAction.Noop)

        # Validate parameters based on action
        self.site = kwargs.get('site', '')

        if self.site == '':
            raise ValueError("Orchestration Task requires 'site' parameter")

        if self.action in [OrchestratorAction.VerifyNode,
                      OrchestratorAction.PrepareNode,
                      OrchestratorAction.DeployNode,
                      OrchestratorAction.DestroyNode]:
            self.node_filter = kwargs.get('node_filter', None)
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

        parent_task = kwargs.get('parent_task','')

        # A lock to prevent concurrency race conditions
        self.update_lock = Lock()

    def get_id(self):
        return self.task_id

    # Mark this task and all subtasks as requested termination
    # so that the task manager knows termination has been requested
    def terminate_task(self):
        locked = self.get_lock()
        if locked:
            # TODO Naively assume subtask termination will succeed for now
            for t in self.subtasks:
                t.terminate_task()
            self.terminate = True
            self.release_lock()
        else:
            raise errors.OrchestratorError("Could not get task update lock")

    def set_status(self, status):
        locked = self.get_lock()
        if locked:
            self.status = status
            self.release_lock()
        else:
            raise errors.OrchestratorError("Could not get task update lock")

    def get_status(self):
        return self.status

    def get_lock(self):
        locked = self.update_lock.acquire(blocking=True, timeout=10)
        return locked

    def release_lock(self):
        self.update_lock.release()
        return

    def create_subtask(self, subtask_class, **kwargs):
        if self.terminate:
            raise errors.OrchestratorError("Cannot create subtask for parent" \
                                           " marked for termination")
        locked = self.get_lock()
        if locked:
            subtask = subtask_class(parent_task=self.get_id(), **kwargs)
            self.subtasks.append(subtask.get_id())
            self.release_lock()
            return subtask
        else:
            raise errors.OrchestratorError("Could not get task update lock")


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
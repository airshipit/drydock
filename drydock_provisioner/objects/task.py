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

import drydock_provisioner.error as errors

import drydock_provisioner.objects.fields as hd_fields

class Task(object):

    def __init__(self, **kwargs):
        self.task_id = uuid.uuid4()
        self.status = hd_fields.TaskStatus.Created
        self.terminate = False
        self.subtasks = []
        self.lock_id = None
        self.result = hd_fields.ActionResult.Incomplete
        self.result_detail = None
        self.action = kwargs.get('action', hd_fields.OrchestratorAction.Noop)

        self.parent_task_id = kwargs.get('parent_task_id','')

    def get_id(self):
        return self.task_id

    def terminate_task(self):
        self.terminate = True

    def set_status(self, status):
        self.status = status

    def get_status(self):
        return self.status

    def set_result(self, result):
        self.result = result

    def get_result(self):
        return self.result

    def set_result_detail(self, detail):
        self.result_detail = detail

    def get_result_detail(self):
        return self.result_detail

    def register_subtask(self, subtask_id):
        if self.terminate:
            raise errors.OrchestratorError("Cannot add subtask for parent" \
                                           " marked for termination")
        self.subtasks.append(subtask_id)

    def get_subtasks(self):
        return self.subtasks

    def to_dict(self):
        return {
            'task_id':  str(self.task_id),
            'action':   self.action,
            'parent_task': str(self.parent_task_id),
            'status':   self.status,
            'result':   self.result,
            'result_detail': self.result_detail,
            'subtasks': [str(x) for x in self.subtasks],
        }

class OrchestratorTask(Task):

    def __init__(self, design_id=None, **kwargs):
        super(OrchestratorTask, self).__init__(**kwargs)

        self.design_id = design_id

        if self.action in [hd_fields.OrchestratorAction.VerifyNode,
                      hd_fields.OrchestratorAction.PrepareNode,
                      hd_fields.OrchestratorAction.DeployNode,
                      hd_fields.OrchestratorAction.DestroyNode]:
            self.node_filter = kwargs.get('node_filter', None)

    def to_dict(self):
        _dict = super(OrchestratorTask, self).to_dict()

        _dict['design_id'] = self.design_id
        _dict['node_filter'] = getattr(self, 'node_filter', None)

        return _dict

class DriverTask(Task):
    def __init__(self, task_scope={}, **kwargs):
        super(DriverTask, self).__init__(**kwargs)

        self.design_id = kwargs.get('design_id', None)

        self.node_list = task_scope.get('node_names', [])

    def to_dict(self):
        _dict = super(DriverTask, self).to_dict()

        _dict['design_id'] = self.design_id
        _dict['node_list'] = self.node_list

        return _dict

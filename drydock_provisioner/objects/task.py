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
"""Models for representing asynchronous tasks."""

import uuid
import datetime

import drydock_provisioner.error as errors

import drydock_provisioner.objects.fields as hd_fields


class Task(object):
    """Asynchronous Task.

    :param action: The enumerated action value to be executed
    :param design_ref: A reference URI to the design data describing the context
                       of this task
    :param parent_task_id: Optional UUID4 ID of the parent task to this task
    :param node_filter: Optional instance of TaskNodeFilter limiting the set of nodes
                        this task will impact
    """

    def __init__(self, **kwargs):
        context = kwargs.get('context', None)

        self.task_id = uuid.uuid4()
        self.status = hd_fields.TaskStatus.Requested
        self.subtask_id_list = []
        self.result = TaskStatus()
        self.action = kwargs.get('action', hd_fields.OrchestratorAction.Noop)
        self.design_ref = kwargs.get('design_ref', None)
        self.parent_task_id = kwargs.get('parent_task_id', None)
        self.created = datetime.utcnow()
        self.node_filter = kwargs.get('node_filter', None)
        self.created_by = None
        self.updated = None
        self.terminated = None
        self.terminated_by = None
        self.context = context

        if context is not None:
            self.created_by = context.user

    def get_id(self):
        return self.task_id

    def terminate_task(self):
        self.set_Status(hd_fields.TaskStatus.Terminating)

    def set_status(self, status):
        self.status = status

    def get_status(self):
        return self.status

    def get_result(self):
        return self.result

    def add_result_message(self, **kwargs):
        """Add a message to result details."""
        self.result.add_message(**kwargs)

    def register_subtask(self, subtask_id):
        if self.status in [hd_fields.TaskStatus.Terminating]:
            raise errors.OrchestratorError("Cannot add subtask for parent"
                                           " marked for termination")
        self.subtask_id_list.append(subtask_id)

    def get_subtasks(self):
        return self.subtask_id_list

    def add_status_msg(self, **kwargs):
        self.result.add_status_msg(**kwargs)

    def to_dict(self):
        return {
            'Kind': 'Task',
            'apiVersion': 'v1',
            'task_id': str(self.task_id),
            'action': self.action,
            'parent_task': str(self.parent_task_id),
            'design_ref': self.design_ref,
            'status': self.status,
            'result': self.result.to_dict(),
            'node_filter': self.node_filter.to_dict(),
            'subtask_id_list': [str(x) for x in self.subtask_id_list],
            'created': self.created,
            'created_by': self.created_by,
            'updated': self.updated,
            'terminated': self.terminated,
            'terminated_by': self.terminated_by,
        }


class TaskStatus(object):
    """Status/Result of this task's execution."""

    def __init__(self):
        self.details = {
            'errorCount': 0,
            'messageList': []
        }

        self.message = None
        self.reason = None
        self.status = hd_fields.ActionResult.Incomplete

    def set_message(self, msg):
        self.message = msg

    def set_reason(self, reason):
        self.reason = reason

    def set_status(self, status):
        self.status = status

    def add_status_msg(self, msg=None, error=None, ctx_type=None, ctx=None, **kwargs):
        if msg is None or error is None or ctx_type is None or ctx is None:
            raise ValueError('Status message requires fields: msg, error, ctx_type, ctx')

        new_msg = TaskStatusMessage(msg, error, ctx_type, ctx, **kwargs)

        self.details.messageList.append(new_msg)

        if error:
            self.details.errorCount = self.details.errorCount + 1

    def to_dict(self):
        return {
            'Kind': 'Status',
            'apiVersion': 'v1',
            'metadata': {},
            'message': self.message,
            'reason': self.reason,
            'status': self.status,
            'details': {
                'errorCount': self.details.errorCount,
                'messageList': [x.to_dict() for x in self.details.messageList],
            }
        }


class TaskStatusMessage(object):
    """Message describing an action or error from executing a Task."""

    def __init__(self, msg, error, ctx_type, ctx, **kwargs):
        self.message = msg
        self.error = error
        self.ctx_type = ctx_type
        self.ctx = ctx
        self.ts = datetime.utcnow()
        self.extra = kwargs

    def to_dict(self):
        _dict = {
            'message': self.message,
            'error': self.error,
            'context_type': self.ctx_type,
            'context': self.ctx,
            'ts': self.ts,
        }

        _dict.update(self.extra)

        return _dict

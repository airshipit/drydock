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
import json

from datetime import datetime

from drydock_provisioner import objects

import drydock_provisioner.error as errors
import drydock_provisioner.objects.fields as hd_fields

from drydock_provisioner.control.base import DrydockRequestContext


class Task(object):
    """Asynchronous Task.

    :param action: The enumerated action value to be executed
    :param design_ref: A reference URI to the design data describing the context
                       of this task
    :param parent_task_id: Optional UUID4 ID of the parent task to this task
    :param node_filter: Optional instance of TaskNodeFilter limiting the set of nodes
                        this task will impact
    :param context: instance of DrydockRequestContext representing the request context the
                    task is executing under
    :param statemgr: instance of AppState used to access the database for state management
    """

    def __init__(self,
                 action=None,
                 design_ref=None,
                 parent_task_id=None,
                 node_filter=None,
                 context=None,
                 statemgr=None):
        self.statemgr = statemgr

        self.task_id = uuid.uuid4()
        self.status = hd_fields.TaskStatus.Requested
        self.subtask_id_list = []
        self.result = TaskStatus()
        self.action = action or hd_fields.OrchestratorAction.Noop
        self.design_ref = design_ref
        self.parent_task_id = parent_task_id
        self.created = datetime.utcnow()
        self.node_filter = node_filter
        self.created_by = None
        self.updated = None
        self.terminated = None
        self.terminated_by = None
        self.request_context = context

        if context is not None:
            self.created_by = context.user

    @classmethod
    def obj_name(cls):
        return cls.__name__

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

    def success(self):
        """Encounter a result that causes at least partial success."""
        if self.result.status in [hd_fields.TaskResult.Failure,
                                  hd_fields.TaskResult.PartialSuccess]:
            self.result.status = hd_fields.TaskResult.PartialSuccess
        else:
            self.result.status = hd_fields.TaskResult.Success

    def failure(self):
        """Encounter a result that causes at least partial failure."""
        if self.result.status in [hd_fields.TaskResult.Success,
                                  hd_fields.TaskResult.PartialSuccess]:
            self.result.status = hd_fields.TaskResult.PartialSuccess
        else:
            self.result.status = hd_fields.TaskResult.Failure

    def register_subtask(self, subtask):
        """Register a task as a subtask to this task.

        :param subtask: objects.Task instance
        """
        if self.status in [hd_fields.TaskStatus.Terminating]:
            raise errors.OrchestratorError("Cannot add subtask for parent"
                                           " marked for termination")
        if self.statemgr.add_subtask(self.task_id, subtask.task_id):
            self.subtask_id_list.append(subtask.task_id)
            subtask.parent_task_id = self.task_id
            subtask.save()
        else:
            raise errors.OrchestratorError("Error adding subtask.")

    def save(self):
        """Save this task's current state to the database."""
        if not self.statemgr.put_task(self):
            raise errors.OrchestratorError("Error saving task.")

    def get_subtasks(self):
        return self.subtask_id_list

    def add_status_msg(self, **kwargs):
        msg = self.result.add_status_msg(**kwargs)
        self.statemgr.post_result_message(self.task_id, msg)

    def to_db(self, include_id=True):
        """Convert this instance to a dictionary for use persisting to a db.

        include_id=False can be used for doing an update where the primary key
        of the table shouldn't included in the values set

        :param include_id: Whether to include task_id in the dictionary
        """
        _dict = {
            'parent_task_id':
            self.parent_task_id.bytes
            if self.parent_task_id is not None else None,
            'subtask_id_list': [x.bytes for x in self.subtask_id_list],
            'result_status':
            self.result.status,
            'result_message':
            self.result.message,
            'result_reason':
            self.result.reason,
            'result_error_count':
            self.result.error_count,
            'status':
            self.status,
            'created':
            self.created,
            'created_by':
            self.created_by,
            'updated':
            self.updated,
            'design_ref':
            self.design_ref,
            'request_context':
            json.dumps(self.request_context.to_dict())
            if self.request_context is not None else None,
            'action':
            self.action,
            'terminated':
            self.terminated,
            'terminated_by':
            self.terminated_by,
        }

        if include_id:
            _dict['task_id'] = self.task_id.bytes

        return _dict

    def to_dict(self):
        """Convert this instance to a dictionary.

        Intended for use in JSON serialization
        """
        return {
            'Kind': 'Task',
            'apiVersion': 'v1',
            'task_id': str(self.task_id),
            'action': self.action,
            'parent_task_id': str(self.parent_task_id),
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

    @classmethod
    def from_db(cls, d):
        """Create an instance from a DB-based dictionary.

        :param d: Dictionary of instance data
        """
        i = Task()

        i.task_id = uuid.UUID(bytes=d.get('task_id'))

        if d.get('parent_task_id', None) is not None:
            i.parent_task_id = uuid.UUID(bytes=d.get('parent_task_id'))

        if d.get('subtask_id_list', None) is not None:
            for t in d.get('subtask_id_list'):
                i.subtask_id_list.append(uuid.UUID(bytes=t))

        simple_fields = [
            'status', 'created', 'created_by', 'design_ref', 'action',
            'terminated', 'terminated_by'
        ]

        for f in simple_fields:
            setattr(i, f, d.get(f, None))

        # Deserialize the request context for this task
        if i.request_context is not None:
            i.request_context = DrydockRequestContext.from_dict(
                i.request_context)

        return i


class TaskStatus(object):
    """Status/Result of this task's execution."""

    def __init__(self):
        self.error_count = 0
        self.message_list = []

        self.message = None
        self.reason = None
        self.status = hd_fields.ActionResult.Incomplete

    @classmethod
    def obj_name(cls):
        return cls.__name__

    def set_message(self, msg):
        self.message = msg

    def set_reason(self, reason):
        self.reason = reason

    def set_status(self, status):
        self.status = status

    def add_status_msg(self,
                       msg=None,
                       error=None,
                       ctx_type=None,
                       ctx=None,
                       **kwargs):
        if msg is None or error is None or ctx_type is None or ctx is None:
            raise ValueError(
                'Status message requires fields: msg, error, ctx_type, ctx')

        new_msg = TaskStatusMessage(msg, error, ctx_type, ctx, **kwargs)

        self.message_list.append(new_msg)

        if error:
            self.error_count = self.error_count + 1

        return new_msg

    def to_dict(self):
        return {
            'Kind': 'Status',
            'apiVersion': 'v1',
            'metadata': {},
            'message': self.message,
            'reason': self.reason,
            'status': self.status,
            'details': {
                'errorCount': self.error_count,
                'messageList': [x.to_dict() for x in self.message_list],
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

    @classmethod
    def obj_name(cls):
        return cls.__name__

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

    def to_db(self):
        """Convert this instance to a dictionary appropriate for the DB."""
        return {
            'message': self.message,
            'error': self.error,
            'context': self.ctx,
            'context_type': self.ctx_type,
            'ts': self.ts,
            'extra': json.dumps(self.extra),
        }

    @classmethod
    def from_db(cls, d):
        """Create instance from DB-based dictionary.

        :param d: dictionary of values
        """
        i = TaskStatusMessage(
            d.get('message', None),
            d.get('error'),
            d.get('context_type'), d.get('context'))
        if 'extra' in d:
            i.extra = d.get('extra')
        i.ts = d.get('ts', None)

        return i


# Emulate OVO object registration
setattr(objects, Task.obj_name(), Task)
setattr(objects, TaskStatus.obj_name(), TaskStatus)
setattr(objects, TaskStatusMessage.obj_name(), TaskStatusMessage)

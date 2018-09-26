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
import time
import logging
import copy

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
    :param retry: integer retry sequence
    """

    def __init__(self,
                 action=None,
                 design_ref=None,
                 parent_task_id=None,
                 node_filter=None,
                 context=None,
                 statemgr=None,
                 retry=0):
        self.statemgr = statemgr

        self.task_id = uuid.uuid4()
        self.status = hd_fields.TaskStatus.Requested
        self.subtask_id_list = []
        self.result = TaskStatus()
        self.action = action or hd_fields.OrchestratorAction.Noop
        self.design_ref = design_ref
        self.retry = retry
        self.parent_task_id = parent_task_id
        self.created = datetime.utcnow()
        self.node_filter = copy.deepcopy(node_filter)
        self.created_by = None
        self.updated = None
        self.terminated = None
        self.terminated_by = None
        self.request_context = context
        self.terminate = False
        self.logger = logging.getLogger("drydock")

        if context is not None:
            self.created_by = context.user

    @classmethod
    def obj_name(cls):
        return cls.__name__

    def get_id(self):
        return self.task_id

    def retry_task(self, max_attempts=None):
        """Check if this task should be retried and update attributes if so.

        :param max_attempts: The maximum number of retries for this task
        """
        if (self.result.status != hd_fields.ActionResult.Success) and (len(
                self.result.failures) > 0):
            if not max_attempts or (max_attempts
                                    and self.retry < max_attempts):
                self.add_status_msg(
                    msg="Retrying task for failed entities.",
                    error=False,
                    ctx='NA',
                    ctx_type='NA')
                self.retry = self.retry + 1
                if len(self.result.successes) > 0:
                    self.result.status = hd_fields.ActionResult.Success
                else:
                    self.result.status = hd_fields.ActionResult.Incomplete
                self.save()
                return True
            else:
                self.add_status_msg(
                    msg="Retry requested, out of attempts.",
                    error=False,
                    ctx='NA',
                    ctx_type='NA')
                raise errors.MaxRetriesReached("Retries reached max attempts.")
        else:
            return False

    def terminate_task(self, terminated_by=None):
        """Terminate this task.

        If the task is queued, just mark it terminated. Otherwise mark it as
        terminating and let the orchestrator manage completing termination.
        """
        self.terminate = True
        self.terminated = datetime.utcnow()
        self.terminated_by = terminated_by
        self.save()

    def check_terminate(self):
        """Check if execution of this task should terminate."""
        return self.terminate

    def set_status(self, status):
        self.status = status

    def get_status(self):
        return self.status

    def get_result(self):
        return self.result.status

    def success(self, focus=None):
        """Encounter a result that causes at least partial success.

        If defined, focus will be added to the task successes list

        :param focus: The entity successfully operated upon
        """
        if self.result.status in [
                hd_fields.ActionResult.Failure,
                hd_fields.ActionResult.PartialSuccess
        ]:
            self.result.status = hd_fields.ActionResult.PartialSuccess
        else:
            self.result.status = hd_fields.ActionResult.Success
        if focus:
            self.logger.debug("Adding %s to successes list." % focus)
            self.result.add_success(focus)

    def failure(self, focus=None):
        """Encounter a result that causes at least partial failure.

        If defined, focus will be added to the task failures list

        :param focus: The entity successfully operated upon
        """
        if self.result.status in [
                hd_fields.ActionResult.Success,
                hd_fields.ActionResult.PartialSuccess
        ]:
            self.result.status = hd_fields.ActionResult.PartialSuccess
        else:
            self.result.status = hd_fields.ActionResult.Failure
        if focus:
            self.logger.debug("Adding %s to failures list." % focus)
            self.result.add_failure(focus)

    def register_subtask(self, subtask):
        """Register a task as a subtask to this task.

        :param subtask: objects.Task instance
        """
        if self.status in [hd_fields.TaskStatus.Terminating]:
            raise errors.OrchestratorError("Cannot add subtask for parent"
                                           " marked for termination")
        if self.statemgr.add_subtask(self.task_id, subtask.task_id):
            self.add_status_msg(
                msg="Started subtask %s for action %s" % (str(
                    subtask.get_id()), subtask.action),
                error=False,
                ctx=str(self.get_id()),
                ctx_type='task')
            self.subtask_id_list.append(subtask.task_id)
            subtask.parent_task_id = self.task_id
            subtask.save()
        else:
            raise errors.OrchestratorError("Error adding subtask.")

    def save(self):
        """Save this task's current state to the database."""
        chk_task = self.statemgr.get_task(self.get_id())

        if chk_task in [
                hd_fields.TaskStatus.Terminating,
                hd_fields.TaskStatus.Terminated
        ]:
            self.set_status(chk_task.status)

        self.updated = datetime.utcnow()
        if not self.statemgr.put_task(self):
            raise errors.OrchestratorError("Error saving task.")

    def get_subtasks(self):
        """Get list of this task's subtasks."""
        return self.subtask_id_list

    def collect_subtasks(self, action=None, poll_interval=15, timeout=300):
        """Monitor subtasks waiting for completion.

        If action is specified, only watch subtasks executing this action. poll_interval
        and timeout are measured in seconds and used for controlling the monitoring behavior.

        :param action: What subtask action to monitor
        :param poll_interval: How often to load subtask status from the database
        :param timeout: How long to continue monitoring before considering subtasks as hung
        """
        timeleft = timeout
        while timeleft > 0:
            st_list = self.statemgr.get_active_subtasks(self.task_id)
            if len(st_list) == 0:
                return True
            else:
                time.sleep(poll_interval)
                timeleft = timeleft - poll_interval

        raise errors.CollectTaskTimeout(
            "Timed out collecting subtasks for task %s." % str(self.task_id))

    def node_filter_from_successes(self):
        """Create a node filter from successful entities in this task's results."""
        nf = dict(filter_set_type='intersection', filter_set=[])
        nf['filter_set'].append(
            dict(node_names=self.result.successes, filter_type='union'))

        return nf

    def node_filter_from_failures(self):
        """Create a node filter from failure entities in this task's result."""
        nf = dict(filter_set_type='intersection', filter_set=[])
        nf['filter_set'].append(
            dict(node_names=self.result.failures, filter_type='union'))

        return nf

    def bubble_results(self, action_filter=None):
        """Combine successes and failures of subtasks and update this task with the result.

        Query all completed subtasks of this task and collect the success and failure entities
        from the subtask result. If action_filter is specified, collect results only from
        subtasks performing the given action. Replace this task's result failures and successes
        with the results of the query. If this task has a ``retry`` sequence greater than 0,
        collect failures from subtasks only with an equivalent retry sequence.

        :param action_filter: string action name to filter subtasks on
        """
        self.logger.debug(
            "Bubbling subtask results up to task %s." % str(self.task_id))
        self.result.successes = []
        self.result.failures = []
        for st in self.statemgr.get_complete_subtasks(self.task_id):
            # Only filters successes.
            if action_filter is None or (action_filter is not None
                                         and st.action == action_filter):
                for se in st.result.successes:
                    self.logger.debug(
                        "Bubbling subtask success for entity %s." % se)
                    self.result.add_success(se)
            else:
                self.logger.debug(
                    "Skipping subtask success due to action filter.")
            # All failures are bubbled up.
            if self.retry == 0 or (self.retry == st.retry):
                for fe in st.result.failures:
                    self.logger.debug(
                        "Bubbling subtask failure for entity %s." % fe)
                    self.result.add_failure(fe)
            else:
                self.logger.debug(
                    "Skipping failures as they mismatch task retry sequence.")

    def align_result(self, action_filter=None, reset_status=True):
        """Align the result of this task with the combined results of all the subtasks.

        If this task has a retry counter > 0, then failure or partial_success results
        of a subtask are only counted if the subtask retry counter is equivalent to this
        task.

        :param action_filter: string action name to filter subtasks on
        :param reset_status: Whether to reset the result status of this task before aligning
        """
        if reset_status:
            # Defaults the ActionResult to Success if there are no tasks
            if not self.statemgr.get_all_subtasks(self.task_id):
                self.result.status = hd_fields.ActionResult.Success
            else:
                self.result.status = hd_fields.ActionResult.Incomplete
        for st in self.statemgr.get_complete_subtasks(self.task_id):
            if action_filter is None or (action_filter is not None
                                         and st.action == action_filter):
                self.logger.debug("Collecting result status from subtask %s." %
                                  str(st.task_id))
                if st.get_result() in [
                        hd_fields.ActionResult.Success,
                        hd_fields.ActionResult.PartialSuccess
                ]:
                    self.success()
                if (st.get_result() in [
                        hd_fields.ActionResult.Failure,
                        hd_fields.ActionResult.PartialSuccess
                ] and (self.retry == 0 or (self.retry == st.retry))):
                    self.failure()
            else:
                self.logger.debug("Skipping subtask %s due to action filter." %
                                  str(st.task_id))

    def add_status_msg(self, **kwargs):
        """Add a status message to this task's result status."""
        msg = self.result.add_status_msg(**kwargs)
        self.statemgr.post_result_message(self.task_id, msg)

    def merge_status_messages(self, task=None, task_result=None):
        """Merge status messages into this task's result status.

        Specify either task or task_result to source status messages from.

        :param task: instance of objects.task.Task to consume result messages from
        :param task_result: instance of objects.task.TaskStatus to consume result message from
        """
        if task:
            msg_list = task.result.message_list
        elif task_result:
            msg_list = task_result.message_list

        for m in msg_list:
            self.add_status_msg(
                msg=m.msg,
                error=m.error,
                ctx_type=m.ctx_type,
                ctx=m.ctx,
                ts=m.ts,
                **m.extra)

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
            'result_successes':
            self.result.successes,
            'result_failures':
            self.result.failures,
            'result_links':
            self.result.links,
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
            'node_filter':
            self.node_filter,
            'action':
            self.action,
            'terminated':
            self.terminated,
            'terminated_by':
            self.terminated_by,
            'terminate':
            self.terminate,
            'retry':
            self.retry
        }

        if include_id:
            _dict['task_id'] = self.task_id.bytes

        return _dict

    def to_dict(self):
        """Convert this instance to a dictionary.

        Intended for use in JSON serialization
        """
        return {
            'kind':
            'Task',
            'apiVersion':
            'v1',
            'task_id':
            str(self.task_id),
            'action':
            self.action,
            'parent_task_id':
            None if self.parent_task_id is None else str(self.parent_task_id),
            'design_ref':
            self.design_ref,
            'status':
            self.status,
            'result':
            self.result.to_dict(),
            'node_filter':
            None if self.node_filter is None else self.node_filter,
            'subtask_id_list': [str(x) for x in self.subtask_id_list],
            'created':
            None if self.created is None else str(self.created),
            'created_by':
            self.created_by,
            'updated':
            None if self.updated is None else str(self.updated),
            'terminated':
            None if self.terminated is None else str(self.terminated),
            'terminated_by':
            self.terminated_by,
            'terminate':
            self.terminate,
            'retry':
            self.retry,
        }

    @classmethod
    def from_db(cls, d):
        """Create an instance from a DB-based dictionary.

        :param d: Dictionary of instance data
        """
        i = Task()

        i.task_id = uuid.UUID(bytes=bytes(d.get('task_id')))

        if d.get('parent_task_id', None) is not None:
            i.parent_task_id = uuid.UUID(bytes=bytes(d.get('parent_task_id')))

        if d.get('subtask_id_list', None) is not None:
            for t in d.get('subtask_id_list'):
                i.subtask_id_list.append(uuid.UUID(bytes=bytes(t)))

        simple_fields = [
            'status',
            'created',
            'created_by',
            'design_ref',
            'action',
            'terminated',
            'terminated_by',
            'terminate',
            'updated',
            'retry',
            'node_filter',
        ]

        for f in simple_fields:
            setattr(i, f, d.get(f, None))

        # Recreate result
        i.result = TaskStatus()
        i.result.error_count = d.get('result_error_count')
        i.result.message = d.get('result_message')
        i.result.reason = d.get('result_reason')
        i.result.status = d.get('result_status')
        i.result.successes = d.get('result_successes', [])
        i.result.failures = d.get('result_failures', [])
        i.result.links = d.get('result_links', [])

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

        self.links = dict()

        # For tasks operating on multiple contexts (nodes, networks, etc...)
        # track which contexts ended successfully and which failed
        self.successes = []
        self.failures = []

    @classmethod
    def obj_name(cls):
        return cls.__name__

    def add_link(self, relation, uri):
        """Add a external reference link to this status.

        :param str relation: The relation of the link
        :param str uri: A valid URI that references the external content
        """
        self.links.setdefault(relation, [])
        self.links[relation].append(uri)

    def get_links(self, relation=None):
        """Get one or more links of this status.

        If ``relation`` is None, then return all links.

        :param str relation: Return only links that exhibit this relation
        :returns: a list of str URIs or empty list
        """
        if relation:
            return self.links.get(relation, [])
        else:
            all_links = list()
            for v in self.links.values():
                all_links.extend(v)
            return all_links

    def set_message(self, msg):
        self.message = msg

    def set_reason(self, reason):
        self.reason = reason

    def set_status(self, status):
        self.status = status

    def add_failure(self, entity):
        """Add an entity to the failures list.

        :param entity: String entity name to add
        """
        if entity not in self.failures:
            self.failures.append(entity)

    def add_success(self, entity):
        """Add an entity to the successes list.

        :param entity: String entity name to add
        """
        if entity not in self.successes:
            self.successes.append(entity)

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
        links = list()
        if self.links:
            for k, v in self.links.items():
                for r in v:
                    links.append(dict(rel=k, href=r))
        return {
            'kind': 'Status',
            'apiVersion': 'v1.0',
            'metadata': {},
            'message': self.message,
            'reason': self.reason,
            'status': self.status,
            'successes': self.successes,
            'failures': self.failures,
            'links': links,
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
        if 'ts' not in kwargs:
            self.ts = datetime.utcnow()
        else:
            self.ts = kwargs.pop('ts')
        self.extra = kwargs

    @classmethod
    def obj_name(cls):
        return cls.__name__

    def to_dict(self):
        """Convert to a dictionary in prep for JSON/YAML serialization."""
        _dict = {
            'message': self.message,
            'error': self.error,
            'context_type': self.ctx_type,
            'context': self.ctx,
            'ts': str(self.ts),
            'extra': self.extra,
        }
        return _dict

    def to_db(self):
        """Convert this instance to a dictionary appropriate for the DB."""
        _dict = {
            'message': self.message,
            'error': self.error,
            'context': self.ctx,
            'context_type': self.ctx_type,
            'ts': self.ts,
            'extra': json.dumps(self.extra),
        }

        if len(_dict['message']) > 128:
            _dict['message'] = _dict['message'][:127]

        return _dict

    @classmethod
    def from_db(cls, d):
        """Create instance from DB-based dictionary.

        :param d: dictionary of values
        """
        i = TaskStatusMessage(
            d.get('message', None), d.get('error'), d.get('context_type'),
            d.get('context'))
        if 'extra' in d:
            i.extra = d.get('extra')
        i.ts = d.get('ts', None)

        return i


# Emulate OVO object registration
setattr(objects, Task.obj_name(), Task)
setattr(objects, TaskStatus.obj_name(), TaskStatus)
setattr(objects, TaskStatusMessage.obj_name(), TaskStatusMessage)

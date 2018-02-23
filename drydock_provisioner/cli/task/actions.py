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
"""Actions related to task commands."""
import time

from drydock_provisioner.cli.action import CliAction
from drydock_provisioner.cli.const import TaskStatus


class TaskList(CliAction):  # pylint: disable=too-few-public-methods
    """Action to list tasks."""

    def __init__(self, api_client):
        """Object initializer.

        :param DrydockClient api_client: The api client used for invocation.
        """
        super().__init__(api_client)
        self.logger.debug('TaskList action initialized')

    def invoke(self):
        """Invoke execution of this action."""
        return self.api_client.get_tasks()


class TaskCreate(CliAction):  # pylint: disable=too-few-public-methods
    """Action to create tasks against a design."""

    def __init__(self,
                 api_client,
                 design_ref,
                 action_name=None,
                 node_names=None,
                 rack_names=None,
                 node_tags=None,
                 block=False,
                 poll_interval=15):
        """Object initializer.

        :param DrydockClient api_client: The api client used for invocation.
        :param string design_ref: The URI reference to design documents
        :param string action_name: The name of the action being performed for this task
        :param List node_names: The list of node names to restrict action application
        :param List rack_names: The list of rack names to restrict action application
        :param List node_tags: The list of node tags to restrict action application
        :param bool block: Whether to block CLI exit until task completes
        :param integer poll_interval: Polling interval to query task status
        """
        super().__init__(api_client)
        self.design_ref = design_ref
        self.action_name = action_name
        self.logger.debug('TaskCreate action initialized for design=%s',
                          design_ref)
        self.logger.debug('Action is %s', action_name)

        self.logger.debug("Node names = %s", node_names)
        self.logger.debug("Rack names = %s", rack_names)
        self.logger.debug("Node tags = %s", node_tags)

        self.block = block
        self.poll_interval = poll_interval

        if any([node_names, rack_names, node_tags]):
            filter_items = {'filter_type': 'union'}

            if node_names is not None:
                filter_items['node_names'] = node_names
            if rack_names is not None:
                filter_items['rack_names'] = rack_names
            if node_tags is None:
                filter_items['node_tags'] = node_tags

            self.node_filter = {
                'filter_set_type': 'intersection',
                'filter_set': [filter_items]
            }
        else:
            self.node_filter = None

    def invoke(self):
        """Invoke execution of this action."""
        task = self.api_client.create_task(
            design_ref=self.design_ref,
            task_action=self.action_name,
            node_filter=self.node_filter)

        if not self.block:
            return task

        task_id = task.get('task_id')

        while True:
            time.sleep(self.poll_interval)
            task = self.api_client.get_task(task_id=task_id)
            if task.get('status',
                        '') in [TaskStatus.Complete, TaskStatus.Terminated]:
                return task


class TaskShow(CliAction):  # pylint: disable=too-few-public-methods
    """Action to show a task's detial."""

    def __init__(self, api_client, task_id, block=False, poll_interval=15):
        """Object initializer.

        :param DrydockClient api_client: The api client used for invocation.
        :param string task_id: the UUID of the task to retrieve
        :param bool block: Whether to block CLI exit until task completes
        :param integer poll_interval: Polling interval to query task status
        """
        super().__init__(api_client)
        self.task_id = task_id
        self.logger.debug('TaskShow action initialized for task_id=%s,',
                          task_id)

        self.block = block
        self.poll_interval = poll_interval

    def invoke(self):
        """Invoke execution of this action."""
        task = self.api_client.get_task(task_id=self.task_id)

        if not self.block:
            return task

        task_id = task.get('task_id')

        while True:
            time.sleep(self.poll_interval)
            task = self.api_client.get_task(task_id=task_id)
            if task.status in [TaskStatus.Complete, TaskStatus.Terminated]:
                return task

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
""" Actions related to task commands
"""

from drydock_provisioner.cli.action import CliAction

class TaskList(CliAction): # pylint: disable=too-few-public-methods
    """ Action to list tasks
    """
    def __init__(self, api_client):
        """
            :param DrydockClient api_client: The api client used for invocation.
        """
        super().__init__(api_client)
        self.logger.debug('TaskList action initialized')

    def invoke(self):
        return self.api_client.get_tasks()

class TaskCreate(CliAction): # pylint: disable=too-few-public-methods
    """ Action to create tasks against a design
    """
    def __init__(self, api_client, design_id, action_name=None, node_names=None, rack_names=None, node_tags=None):
        """
        node_filter : {node_names: [], rack_names:[], node-tags[]}
            :param DrydockClient api_client: The api client used for invocation.
            :param string design_id: The UUID of the design for which to create a task
            :param string action_name: The name of the action being performed for this task
            :param List node_names: The list of node names to restrict action application
            :param List rack_names: The list of rack names to restrict action application
            :param List node_tags: The list of node tags to restrict action application
        """
        super().__init__(api_client)
        self.design_id = design_id
        self.action_name = action_name
        self.logger.debug('TaskCreate action initialized for design=%s', design_id)
        self.logger.debug('Action is %s', action_name)
        if node_names is None:
            node_names = []
        if rack_names is None:
            rack_names = []
        if node_tags is None:
            node_tags = []

        self.logger.debug("Node names = %s", node_names)
        self.logger.debug("Rack names = %s", rack_names)
        self.logger.debug("Node tags = %s", node_tags)

        self.node_filter = {'node_names' : node_names,
                            'rack_names' : rack_names,
                            'node_tags' : node_tags
                           }

    def invoke(self):
        return self.api_client.create_task(design_id=self.design_id,
                                           task_action=self.action_name,
                                           node_filter=self.node_filter)

class TaskShow(CliAction): # pylint: disable=too-few-public-methods
    """ Action to show a task's detial.
    """
    def __init__(self, api_client, task_id):
        """
            :param DrydockClient api_client: The api client used for invocation.
            :param string task_id: the UUID of the task to retrieve
        """
        super().__init__(api_client)
        self.task_id = task_id
        self.logger.debug('TaskShow action initialized for task_id=%s,', task_id)

    def invoke(self):
        return self.api_client.get_task(task_id=self.task_id)

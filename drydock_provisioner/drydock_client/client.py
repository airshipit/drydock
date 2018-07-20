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
"""REST client for Drydock API."""

import logging

from drydock_provisioner import error as errors


class DrydockClient(object):
    """"
    A client for the Drydock API

    :param DrydockSession session: A instance of DrydockSession to be used by this client
    """

    def __init__(self, session):
        self.session = session
        self.logger = logging.getLogger(__name__)

    def get_task_build_data(self, task_id):
        """Get the build data associated with ``task_id``.

        :param str task_id: A UUID-formatted task ID
        :return: A list of dictionaries resembling objects.builddata.BuildData
        """
        endpoint = 'v1.0/tasks/{}/builddata'.format(task_id)

        resp = self.session.get(endpoint)
        self._check_response(resp)
        return resp.json()

    def get_node_build_data(self, nodename, latest=True):
        """Get the build data associated with ``nodename``.

        :param str nodename: Name of the node
        :param bool latest: Whether to request only the latest version of each data item
        :return: A list of dictionaries resembling objects.builddata.BuildData
        """
        endpoint = 'v1.0/nodes/{}/builddata?latest={}'.format(nodename, latest)

        resp = self.session.get(endpoint)
        self._check_response(resp)
        return resp.json()

    def get_nodes(self):
        """Get list of nodes in MaaS and their status."""
        endpoint = 'v1.0/nodes'

        resp = self.session.get(endpoint)

        self._check_response(resp)

        return resp.json()

    def get_nodes_for_filter(self, design_ref, node_filter=None):
        """Get list of nodes in MaaS and their status.

        :param SiteDesign design_ref: A SiteDesign object.
        :param NodeFilter node_filter (optional): A NodeFilter object.
        :return: A list of node names based on the node_filter and design_ref.
        """
        endpoint = 'v1.0/nodefilter'
        body = {'node_filter': node_filter, 'design_ref': design_ref}
        resp = self.session.post(endpoint, data=body)

        self._check_response(resp)

        return resp.json()

    def get_tasks(self):
        """
        Get a list of all the tasks, completed or running.

        :return: List of string uuid task IDs
        """

        endpoint = "v1.0/tasks"

        resp = self.session.get(endpoint)

        self._check_response(resp)

        return resp.json()

    def get_task(self,
                 task_id,
                 builddata=None,
                 subtaskerrors=None,
                 layers=None):
        """
        Get the current description of a Drydock task

        :param string task_id: The string uuid task id to query.
        :param boolean builddata: If true will include the build_data in the response.
        :param boolean subtaskerrors: If true it will add all the errors from the subtasks as a dictionary in
                                      subtask_errors.
        :param int layers: If -1 will include all subtasks, if a positive integer it will include that many layers
                           of subtasks.
        :return: A dict representing the current state of the task.
        """

        endpoint = "v1.0/tasks/%s" % (task_id)

        query_params = []
        if builddata:
            query_params.append('builddata=true')
        if subtaskerrors:
            query_params.append('subtaskerrors=true')
        if layers:
            query_params.append('layers=%s' % layers)
        if query_params:
            endpoint = '%s?%s' % (endpoint, '&'.join(query_params))

        resp = self.session.get(endpoint)

        self._check_response(resp)

        return resp.json()

    def create_task(self, design_ref, task_action, node_filter=None):
        """
        Create a new task in Drydock

        :param string design_ref: A URI reference to the design documents for this task
        :param string task_action: The action that should be executed
        :param dict node_filter: A filter for narrowing the scope of the task. Valid fields are 'node_names',
                                 'rack_names', 'node_tags'.
        :return: The dictionary representation of the created task
        """

        endpoint = 'v1.0/tasks'

        task_dict = {
            'action': task_action,
            'design_ref': design_ref,
            'node_filter': node_filter,
        }

        self.logger.debug("drydock_client is calling %s API: body is %s" %
                          (endpoint, str(task_dict)))

        resp = self.session.post(endpoint, data=task_dict)

        self._check_response(resp)

        return resp.json()

    def validate_design(self, href):
        """Get list of nodes in MaaS and their status.

        :param href: A href that points to the design_ref.
        :return: A dict containing the validation.
        """
        endpoint = 'v1.0/validatedesign'
        body = {'href': href}
        resp = self.session.post(endpoint, data=body)

        self._check_response(resp)

        return resp.json()

    def _check_response(self, resp):
        if resp.status_code == 401:
            raise errors.ClientUnauthorizedError(
                "Unauthorized access to %s, include valid token." % resp.url)
        elif resp.status_code == 403:
            raise errors.ClientForbiddenError(
                "Forbidden access to %s" % resp.url)
        elif not resp.ok:
            raise errors.ClientError(
                "Error - received %d: %s" % (resp.status_code, resp.text),
                code=resp.status_code)

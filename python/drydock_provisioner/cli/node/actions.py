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


class NodeList(CliAction):  # pylint: disable=too-few-public-methods
    """ Action to list tasks
    """

    def __init__(self, api_client):
        """
            :param DrydockClient api_client: The api client used for invocation.
        """
        super().__init__(api_client)
        self.logger.debug('NodeList action initialized')

    def invoke(self):
        return self.api_client.get_nodes()


class NodeBuildData(CliAction):
    """ Action to print node build data."""

    def __init__(self, api_client, nodename, latest):
        """
        :param DrydockClient api_client: the api client used for invocation.
        :param str nodename: The name of the node to retrieve data for.
        :param bool latest: If only the latest build data should be retrieved.
        """
        super().__init__(api_client)
        self.nodename = nodename
        self.latest = latest
        self.logger.debug('NodeBuildData action initialized')

    def invoke(self):
        return self.api_client.get_node_build_data(self.nodename,
                                                   latest=self.latest)

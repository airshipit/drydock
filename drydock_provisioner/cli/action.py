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
""" Base classes for cli actions intended to invoke the api
"""
import logging

class CliAction: # pylint: disable=too-few-public-methods
    """ Action base for CliActions
    """
    def __init__(self, api_client):
        self.logger = logging.getLogger('drydock_cli')
        self.api_client = api_client
        self.logger.debug("Action initialized with client %s", self.api_client.session.host)

    def invoke(self):
        """ The action to be taken. By default, this is not implemented
        """
        raise NotImplementedError("Invoke method has not been implemented")

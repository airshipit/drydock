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
""" Actions related to part command
"""


from drydock_provisioner.cli.action import CliAction

class PartBase(CliAction): # pylint: disable=too-few-public-methods
    """ base class to set up part actions requiring a design_id
    """
    def __init__(self, api_client, design_id):
        super().__init__(api_client)
        self.design_id = design_id
        self.logger.debug('Initializing a Part action with design_id=%s', design_id)

class PartList(PartBase): # pylint: disable=too-few-public-methods
    """ Action to list parts of a design
    """
    def __init__(self, api_client, design_id):
        """
            :param DrydockClient api_client: The api client used for invocation.
            :param string design_id: The UUID of the design for which to list parts
        """
        super().__init__(api_client, design_id)
        self.logger.debug('PartList action initialized')

    def invoke(self):
        #TODO: change the api call
        return 'This function does not yet have an implementation to support the request'

class PartCreate(PartBase): # pylint: disable=too-few-public-methods
    """ Action to create parts of a design
    """
    def __init__(self, api_client, design_id, in_file):
        """
            :param DrydockClient api_client: The api client used for invocation.
            :param string design_id: The UUID of the design for which to create a part
            :param in_file: The file containing the specification of the part
        """
        super().__init__(api_client, design_id)
        self.in_file = in_file
        self.logger.debug('PartCreate action init. Input file (trunc to 100 chars)=%s', in_file[:100])

    def invoke(self):
        return self.api_client.load_parts(self.design_id, self.in_file)

class PartShow(PartBase): # pylint: disable=too-few-public-methods
    """ Action to show a part of a design.
    """
    def __init__(self, api_client, design_id, kind, key, source='designed'):
        """
            :param DrydockClient api_client: The api client used for invocation.
            :param string design_id: the UUID of the design containing this part
            :param string kind: the string represesnting the 'kind' of the document to return
            :param string key: the string representing the key of the document to return.
            :param string source: 'designed' (default) if this is the designed version,
                                  'compiled' if the compiled version (after merging)
        """
        super().__init__(api_client, design_id)
        self.kind = kind
        self.key = key
        self.source = source
        self.logger.debug('DesignShow action initialized for design_id=%s,'
                          ' kind=%s, key=%s, source=%s',
                          design_id,
                          kind,
                          key,
                          source)

    def invoke(self):
        return self.api_client.get_part(design_id=self.design_id,
                                        kind=self.kind,
                                        key=self.key,
                                        source=self.source)

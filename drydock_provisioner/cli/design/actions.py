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
""" Actions related to design
"""
from drydock_provisioner.cli.action import CliAction

class DesignList(CliAction): # pylint: disable=too-few-public-methods
    """ Action to list designs
    """
    def __init__(self, api_client):
        super().__init__(api_client)
        self.logger.debug("DesignList action initialized")

    def invoke(self):
        return self.api_client.get_design_ids()

class DesignCreate(CliAction): # pylint: disable=too-few-public-methods
    """ Action to create designs
    """
    def __init__(self, api_client, base_design=None):
        """
            :param string base_design: A UUID of the base design to model after
        """
        super().__init__(api_client)
        self.logger.debug("DesignCreate action initialized with base_design=%s", base_design)
        self.base_design = base_design

    def invoke(self):
        return self.api_client.create_design(base_design=self.base_design)


class DesignShow(CliAction): # pylint: disable=too-few-public-methods
    """ Action to show a design.
        :param string design_id: A UUID design_id
        :param string source: (Optional) The model source to return. 'designed' is as input,
                              'compiled' is after merging
    """
    def __init__(self, api_client, design_id, source='designed'):
        super().__init__(api_client)
        self.design_id = design_id
        self.source = source
        self.logger.debug("DesignShow action initialized for design_id = %s", design_id)

    def invoke(self):
        return self.api_client.get_design(design_id=self.design_id, source=self.source)

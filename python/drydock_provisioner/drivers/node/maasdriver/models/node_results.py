# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
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
"""Model for MaaS Node Result resources."""
import base64
import binascii

import drydock_provisioner.drivers.node.maasdriver.models.base as model_base


class NodeResult(model_base.ResourceBase):

    resource_url = 'commissioning-results/'
    fields = [
        'resource_id', 'name', 'result_type', 'updated', 'data',
        'script_result'
    ]
    json_fields = []

    type_map = {
        'commissioning': 0,
        'deploy': 1,
        'testing': 2,
    }

    type_rev_map = {
        0: 'commissioning',
        1: 'deploy',
        2: 'testing',
    }

    def __init__(self, api_client, **kwargs):
        super().__init__(api_client, **kwargs)

    def refresh(self):
        """Don't allow refresh of individual result."""
        return

    def update(self):
        """Don't allow updates."""
        return

    def get_decoded_data(self):
        """Decode the result data from base64."""
        try:
            return base64.b64decode(self.data)
        except binascii.Error:
            return None

    def get_type_desc(self):
        return NodeResult.type_rev_map.get(self.result_type)


class NodeResults(model_base.ResourceCollectionBase):

    collection_url = 'commissioning-results/'
    collection_resource = NodeResult

    def __init__(self, api_client, system_id_list=None, result_type=None):
        super().__init__(api_client)

        self.system_id_list = system_id_list
        self.result_type = result_type

    def refresh(self):
        params = dict()
        if self.system_id_list:
            params['system_id'] = self.system_id_list
        if self.result_type and self.result_type != 'all':
            params['result_type'] = NodeResult.type_map.get(self.result_type)

        url = self.interpolate_url()

        if params:
            resp = self.api_client.get(url, files=params)
        else:
            resp = self.api_client.get(url)

        if resp.status_code in [200]:
            json_list = resp.json()
            self.resource = dict()

            for o in json_list:
                if isinstance(o, dict):
                    i = self.collection_resource.from_dict(self.api_client, o)
                    self.resources[i.resource_id] = i

        return

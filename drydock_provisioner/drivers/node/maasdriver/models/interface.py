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

import drydock_provisioner.drivers.node.maasdriver.models.base as model_base

class Interface(model_base.ResourceBase):

    resource_url = 'nodes/{system_id}/interfaces/{resource_id}/'
    fields = ['resource_id', 'system_id', 'name', 'type', 'mac_address', 'vlan',
              'links', 'effective_mtu']
    json_fields = ['name', 'type', 'mac_address', 'vlan', 'links', 'effective_mtu']

    def __init__(self, api_client, **kwargs):
        super(Interface, self).__init__(api_client, **kwargs)

class Interfaces(model_base.ResourceCollectionBase):

    collection_url = 'nodes/{system_id}/interfaces/'
    collection_resource = Interface

    def __init__(self, api_client, **kwargs):
        super(Interfaces, self).__init__(api_client)
        self.system_id = kwargs.get('system_id', None)
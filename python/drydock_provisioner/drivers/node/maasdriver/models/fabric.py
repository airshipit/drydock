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
"""Models for MaaS Fabric resources."""

import drydock_provisioner.drivers.node.maasdriver.models.base as model_base
import drydock_provisioner.drivers.node.maasdriver.models.vlan as model_vlan


class Fabric(model_base.ResourceBase):

    resource_url = 'fabrics/{resource_id}/'
    fields = ['resource_id', 'name', 'description']
    json_fields = ['name', 'description']

    def __init__(self, api_client, **kwargs):
        super(Fabric, self).__init__(api_client, **kwargs)

        if getattr(self, 'resource_id', None):
            self.refresh_vlans()

    def refresh(self):
        super(Fabric, self).refresh()

        self.refresh_vlans()

        return

    def refresh_vlans(self):
        self.vlans = model_vlan.Vlans(
            self.api_client, fabric_id=self.resource_id)
        self.vlans.refresh()

    def set_resource_id(self, res_id):
        self.resource_id = res_id
        self.refresh_vlans()


class Fabrics(model_base.ResourceCollectionBase):

    collection_url = 'fabrics/'
    collection_resource = Fabric

    def __init__(self, api_client):
        super(Fabrics, self).__init__(api_client)

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

import helm_drydock.drivers.node.maasdriver.models.base as model_base

class Subnet(model_base.ResourceBase):

    resource_url = 'subnets/{resource_id}/'
    fields = ['resource_id', 'name', 'description', 'fabric', 'vlan', 'vid', 'dhcp_on',
              'space', 'cidr', 'gateway_ip', 'rdns_mode', 'allow_proxy', 'dns_servers']
    json_fields = ['name', 'description','vlan', 'space', 'cidr', 'gateway_ip', 'rdns_mode',
                   'allow_proxy', 'dns_servers']

    def __init__(self, api_client, **kwargs):
        super(Subnet, self).__init__(api_client, **kwargs)

        # For now all subnets will be part of the default space
        self.space = 0

    """
    Because MaaS decides to replace the VLAN id with the
    representation of the VLAN, we must reverse it for a true
    representation of the resource
    """
    @classmethod
    def from_dict(cls, api_client, obj_dict):
        refined_dict = {k: obj_dict.get(k, None) for k in cls.fields}
        if 'id' in obj_dict.keys():
            refined_dict['resource_id'] = obj_dict.get('id')

        if isinstance(refined_dict.get('vlan', None), dict):
            refined_dict['fabric'] = refined_dict['vlan']['fabric_id']
            refined_dict['vlan'] = refined_dict['vlan']['id']
            
        i = cls(api_client, **refined_dict)
        return i

class Subnets(model_base.ResourceCollectionBase):

    collection_url = 'subnets/'
    collection_resource = Subnet

    def __init__(self, api_client, **kwargs):
        super(Subnets, self).__init__(api_client)

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

class IpRange(model_base.ResourceBase):

    resource_url = 'iprange/{resource_id}/'
    fields = ['resource_id', 'comment', 'subnet', 'type', 'start_ip', 'end_ip']
    json_fields = ['comment','start_ip', 'end_ip']

    def __init__(self, api_client, **kwargs):
        super(IpRange, self).__init__(api_client, **kwargs)

    @classmethod
    def from_dict(cls, api_client, obj_dict):
        refined_dict = {k: obj_dict.get(k, None) for k in cls.fields}
        if 'id' in obj_dict.keys():
            refined_dict['resource_id'] = obj_dict.get('id')

        if isinstance(refined_dict.get('subnet', None), dict):
            refined_dict['subnet'] = refined_dict['subnet']['id']
            
        i = cls(api_client, **refined_dict)
        return i

class IpRanges(model_base.ResourceCollectionBase):

    collection_url = 'ipranges/'
    collection_resource = IpRange

    def __init__(self, api_client, **kwargs):
        super(IpRanges, self).__init__(api_client, **kwargs)

    def add(self, res):
        """
        Custom add to include a subnet id and type which can't be
        updated in a PUT
        """
        data_dict = res.to_dict()

        subnet = getattr(res, 'subnet', None)

        if subnet is not None:
            data_dict['subnet'] = subnet

        range_type = getattr(res, 'type', None)

        if range_type is not None:
            data_dict['type'] = range_type
            
        url = self.interpolate_url()

        resp = self.api_client.post(url, files=data_dict)

        if resp.status_code == 200:
            resp_json = resp.json()
            res.set_resource_id(resp_json.get('id'))
            return res
        
        raise errors.DriverError("Failed updating MAAS url %s - return code %s"
                % (url, resp.status_code))

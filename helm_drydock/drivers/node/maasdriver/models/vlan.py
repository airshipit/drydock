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
import json

import helm_drydock.error as errors
import helm_drydock.drivers.node.maasdriver.models.base as model_base

class Vlan(model_base.ResourceBase):

    resource_url = 'fabrics/{fabric_id}/vlans/{api_id}/'
    fields = ['resource_id', 'name', 'description', 'vid', 'fabric_id', 'dhcp_on', 'mtu']
    json_fields = ['name', 'description', 'vid', 'dhcp_on', 'mtu']

    def __init__(self, api_client, **kwargs):
        super(Vlan, self).__init__(api_client, **kwargs)

        if self.vid is None:
            self.vid = 0

        # the MaaS API decided that the URL endpoint for VLANs should use
        # the VLAN tag (vid) rather than the resource ID. So to update the 
        # vid, we have to keep two copies so that the resource_url
        # is accurate for updates
        self.api_id = self.vid

    def update(self):
        super(Vlan, self).update()

        self.api_id = self.vid

    def set_vid(self, new_vid):
        if new_vid is None:
            self.vid = 0
        else:
            self.vid = int(new_vid)

class Vlans(model_base.ResourceCollectionBase):

    collection_url = 'fabrics/{fabric_id}/vlans/'
    collection_resource = Vlan

    def __init__(self, api_client, **kwargs):
        super(Vlans, self).__init__(api_client)

        self.fabric_id = kwargs.get('fabric_id', None)
    """
    Create a new resource in this collection in MaaS
    def add(self, res):
        #MAAS API doesn't support all attributes in POST, so create and
        # then promptly update via PUT

        min_fields = {
            'name':   res.name,
            'description':  getattr(res, 'description', None),
        }
         
        if getattr(res, 'vid', None) is None:
            min_fields['vid'] = 0
        else:
            min_fields['vid'] = res.vid

        url = self.interpolate_url()
        resp = self.api_client.post(url, files=min_fields)

        # Check on initial POST creation
        if resp.status_code == 200:
            resp_json = resp.json()
            res.id = resp_json.get('id')
            # Submit PUT for additonal fields
            res.update()
            return res
        
        raise errors.DriverError("Failed updating MAAS url %s - return code %s\n%s"
                % (url, resp.status_code, resp.text))
    """
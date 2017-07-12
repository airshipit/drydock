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

import drydock_provisioner.error as errors
import drydock_provisioner.drivers.node.maasdriver.models.base as model_base

import yaml

class Tag(model_base.ResourceBase):

    resource_url = 'tags/{resource_id}/'
    fields = ['resource_id', 'name', 'defintion', 'kernel_opts']
    json_fields = ['name','kernel_opts', 'comment', 'definition']

    def __init__(self, api_client, **kwargs):
        super(Tag, self).__init__(api_client, **kwargs)

    def get_applied_nodes(self):
        """
        Query the list of nodes this tag is currently applied to

        :return: List of MaaS system_ids of nodes
        """

        url = self.interpolate_url()

        resp = self.api_client.get(url, op='nodes')

        if resp.status_code == 200:
            resp_json = resp.json()
            system_id_list = []

            for n in resp_json:
                system_id = n.get('system_id', None)
                if system_id is not None:
                    system_id_list.append(system_id)

            return system_id_list
        else:
            self.logger.error("Error retrieving node/tag pairs, received HTTP %s from MaaS" % resp.status_code)
            self.logger.debug("MaaS response: %s" % resp.text)
            raise errors.DriverError("Error retrieving node/tag pairs, received HTTP %s from MaaS" % resp.status_code)

    def apply_to_node(self, system_id):
        """
        Apply this tag to a MaaS node

        :param system_id: MaaS system_id of the node
        """

        if system_id in self.get_applied_nodes():
            self.logger.debug("Tag %s already applied to node %s" % (self.name, system_id))
        else:
            url = self.interpolate_url()

            resp = self.api_client.post(url, op='update_nodes', files={'add': system_id})

            if not resp.ok:
                self.logger.error("Error applying tag to node, received HTTP %s from MaaS" % resp.status_code)
                self.logger.debug("MaaS response: %s" % resp.text)
                raise errors.DriverError("Error applying tag to node, received HTTP %s from MaaS" % resp.status_code)

    def to_dict(self):
        """
        Serialize this resource instance into a dict matching the
        MAAS representation of the resource
        """
        data_dict = {}

        for f in self.json_fields:
            if getattr(self, f, None) is not None:
                if f == 'resource_id':
                    data_dict['name'] = getattr(self, f)
                else:
                    data_dict[f] = getattr(self, f)

        return data_dict

    @classmethod
    def from_dict(cls, api_client, obj_dict):
        """
        Create a instance of this resource class based on a dict
        of MaaS type attributes

        Customized for Tag due to use of name instead of id
        as resource key

        :param api_client: Instance of api_client.MaasRequestFactory for accessing MaaS API
        :param obj_dict: Python dict as parsed from MaaS API JSON representing this resource type
        """

        refined_dict = {k: obj_dict.get(k, None) for k in cls.fields}

        if 'name' in obj_dict:
            refined_dict['resource_id'] = obj_dict.get('name')

        i = cls(api_client, **refined_dict)
        return i

class Tags(model_base.ResourceCollectionBase):

    collection_url = 'tags/'
    collection_resource = Tag

    def __init__(self, api_client, **kwargs):
        super(Tags, self).__init__(api_client)

    def add(self, res):
        """
        Create a new resource in this collection in MaaS

        Customize as Tag resources use 'name' instead of 'id'

        :param res: Instance of cls.collection_resource
        """
        data_dict = res.to_dict()
        url = self.interpolate_url()

        resp = self.api_client.post(url, files=data_dict)

        if resp.status_code == 200:
            resp_json = resp.json()
            res.set_resource_id(resp_json.get('name'))
            return res
        elif resp.status_code == 400 and resp.text.find('Tag with this Name already exists.') != -1:
            raise errors.DriverError("Tag %s already exists" % res.name)
        else:
            raise errors.DriverError("Failed updating MAAS url %s - return code %s"
                      % (url, resp.status_code))


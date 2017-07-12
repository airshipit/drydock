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
import re
import logging

import drydock_provisioner.error as errors
"""
A representation of a MaaS REST resource. Should be subclassed
for different resources and augmented with operations specific
to those resources
"""
class ResourceBase(object):

    resource_url = '/{id}'
    fields = ['resource_id']
    json_fields = ['resource_id']

    def __init__(self, api_client, **kwargs):
        self.api_client = api_client
        self.logger = logging.getLogger('drydock.nodedriver.maasdriver')

        for f in self.fields:
            if f in kwargs.keys():
                setattr(self, f, kwargs.get(f))

    """
    Update resource attributes from MaaS
    """
    def refresh(self):
        url = self.interpolate_url()
        resp = self.api_client.get(url)

        updated_fields = resp.json()

        for f in self.fields:
            if f in updated_fields.keys():
                setattr(self, f, updated_fields.get(f))

    """
    Parse URL for placeholders and replace them with current
    instance values
    """
    def interpolate_url(self):
        pattern = '\{([a-z_]+)\}'
        regex = re.compile(pattern)
        start = 0
        new_url = self.resource_url

        while (start+1) < len(self.resource_url):
            match = regex.search(self.resource_url, start)
            if match is None:
                return new_url

            param = match.group(1)
            val = getattr(self, param, None)
            if val is None:
                raise ValueError("Missing variable value")
            new_url = new_url.replace('{' + param + '}', str(val))
            start = match.end(1) + 1

        return new_url

    """
    Update MaaS with current resource attributes
    """
    def update(self):
        data_dict = self.to_dict()
        url = self.interpolate_url()

        resp = self.api_client.put(url, files=data_dict)

        if resp.status_code == 200:
            return True
        
        raise errors.DriverError("Failed updating MAAS url %s - return code %s\n%s"
                % (url, resp.status_code, resp.text))

    """
    Set the resource_id for this instance
    Should only be called when creating new instances and MAAS has assigned
    an id
    """
    def set_resource_id(self, res_id):
        self.resource_id = res_id

    """
    Serialize this resource instance into JSON matching the
    MaaS respresentation of this resource
    """
    def to_json(self):
        return json.dumps(self.to_dict())

    """
    Serialize this resource instance into a dict matching the
    MAAS representation of the resource
    """
    def to_dict(self):
        data_dict = {}

        for f in self.json_fields:
            if getattr(self, f, None) is not None:
                if f == 'resource_id':
                    data_dict['id'] = getattr(self, f)
                else:
                    data_dict[f] = getattr(self, f)

        return data_dict

    """
    Create a instance of this resource class based on the MaaS
    representation of this resource type
    """
    @classmethod
    def from_json(cls, api_client, json_string):
        parsed = json.loads(json_string)

        if isinstance(parsed, dict):
            return cls.from_dict(api_client, parsed)

        raise errors.DriverError("Invalid JSON for class %s" % (cls.__name__))

    """
    Create a instance of this resource class based on a dict
    of MaaS type attributes
    """
    @classmethod
    def from_dict(cls, api_client, obj_dict):
        refined_dict = {k: obj_dict.get(k, None) for k in cls.fields}
        if 'id' in obj_dict.keys():
            refined_dict['resource_id'] = obj_dict.get('id')

        i = cls(api_client, **refined_dict)
        return i


class ResourceCollectionBase(object):
    """
    A collection of MaaS resources.

    Rather than a simple list, we will key the collection on resource
    ID for more efficient access.

    :param api_client: An instance of api_client.MaasRequestFactory
    """

    collection_url = ''
    collection_resource = ResourceBase

    def __init__(self, api_client):
        self.api_client = api_client
        self.resources = {}
        self.logger = logging.getLogger('drydock.nodedriver.maasdriver')

    def interpolate_url(self):
        """
        Parse URL for placeholders and replace them with current
        instance values
        """
        pattern = '\{([a-z_]+)\}'
        regex = re.compile(pattern)
        start = 0
        new_url = self.collection_url

        while (start+1) < len(self.collection_url):
            match = regex.search(self.collection_url, start)
            if match is None:
                return new_url

            param = match.group(1)
            val = getattr(self, param, None)
            if val is None:
                raise ValueError("Missing variable value")
            new_url = new_url.replace('{' + param + '}', str(val))
            start = match.end(1) + 1

        return new_url

    """
    Create a new resource in this collection in MaaS
    """
    def add(self, res):
        data_dict = res.to_dict()
        url = self.interpolate_url()

        resp = self.api_client.post(url, files=data_dict)

        if resp.status_code in [200,201]:
            resp_json = resp.json()
            res.set_resource_id(resp_json.get('id'))
            return res
        
        raise errors.DriverError("Failed updating MAAS url %s - return code %s"
                % (url, resp.status_code))

    """
    Append a resource instance to the list locally only
    """
    def append(self, res):
        if isinstance(res, self.collection_resource):
            self.resources[res.resource_id] = res

    """
    Initialize or refresh the collection list from MaaS
    """
    def refresh(self):
        url = self.interpolate_url()
        resp = self.api_client.get(url)

        if resp.status_code == 200:
            self.resource = {}
            json_list = resp.json()

            for o in json_list:
                if isinstance(o, dict):
                    i = self.collection_resource.from_dict(self.api_client, o)
                    self.resources[i.resource_id] = i

        return

    """
    Check if resource id is in this collection
    """
    def contains(self, res_id):
        if res_id in self.resources.keys():
            return True

        return False

    """
    Select a resource based on ID or None if not found
    """
    def select(self, res_id):
        return self.resources.get(res_id, None)

    """
    Query the collection based on a resource attribute other than primary id
    """
    def query(self, query):
        result = list(self.resources.values())
        for (k, v) in query.items():
            result = [i for i in result
                      if str(getattr(i, k, None)) == str(v)]

        return result

    def singleton(self, query):
        """
        A query that requires a single item response

        :param query: A dict of k:v pairs defining the query parameters
        """
        result = self.query(query)

        if len(result) > 1:
            raise ValueError("Multiple results found")
        elif len(result) == 1:
            return result[0]

        return None
        
    """
    If the collection contains a single item, return it
    """
    def single(self):
        if self.len() == 1:
            for v in self.resources.values():
                return v
        else:
            return None

    """
    Iterate over the resources in the collection
    """
    def __iter__(self):
        return iter(self.resources.values())

    """
    Resource count
    """
    def len(self):
        return len(self.resources)
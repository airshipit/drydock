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
"""Model representing MaaS static routes resource."""

import drydock_provisioner.drivers.node.maasdriver.models.base as model_base


class StaticRoute(model_base.ResourceBase):
    """Model for single static route."""

    resource_url = 'static-routes/{resource_id}/'
    fields = ['resource_id', 'source', 'destination', 'gateway_ip', 'metric']
    json_fields = ['source', 'destination', 'gateway_ip', 'metric']

    def __init__(self, api_client, **kwargs):
        super().__init__(api_client, **kwargs)

    @classmethod
    def from_dict(cls, api_client, obj_dict):
        refined_dict = {k: obj_dict.get(k, None) for k in cls.fields}
        if 'id' in obj_dict.keys():
            refined_dict['resource_id'] = obj_dict.get('id')

        if isinstance(refined_dict.get('source', None), dict):
            refined_dict['source'] = refined_dict['source']['id']

        if isinstance(refined_dict.get('destination', None), dict):
            refined_dict['destination'] = refined_dict['destination']['id']

        i = cls(api_client, **refined_dict)
        return i


class StaticRoutes(model_base.ResourceCollectionBase):
    """Model for a collection of static routes."""

    collection_url = 'static-routes/'
    collection_resource = StaticRoute

    def __init__(self, api_client, **kwargs):
        super().__init__(api_client, **kwargs)

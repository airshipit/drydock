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
"""Model for MaaS Package Repository resources."""

import drydock_provisioner.drivers.node.maasdriver.models.base as model_base


class Repository(model_base.ResourceBase):

    resource_url = 'package-repositories/{resource_id}/'
    fields = [
        'resource_id', 'name', 'url', 'distributions', 'components', 'arches',
        'key', 'enabled'
    ]
    json_fields = [
        'name', 'url', 'distributions', 'components', 'arches', 'key',
        'enabled'
    ]

    def __init__(self, api_client, **kwargs):
        super().__init__(api_client, **kwargs)


class Repositories(model_base.ResourceCollectionBase):

    collection_url = 'package-repositories/'
    collection_resource = Repository

    def __init__(self, api_client):
        super().__init__(api_client)

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
"""Model representing MaaS DNS domain resource."""

import drydock_provisioner.drivers.node.maasdriver.models.base as model_base


class Domain(model_base.ResourceBase):
    """Model for single domain."""

    resource_url = 'domains/{resource_id}/'
    fields = ['resource_id', 'name', 'authoritative', 'ttl']
    json_fields = ['name', 'authoritative', 'ttl']


class Domains(model_base.ResourceCollectionBase):
    """Model for a collection of static routes."""

    collection_url = 'domains/'
    collection_resource = Domain

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
"""Model for MaaS API boot_resource type."""

import drydock_provisioner.error as errors
import drydock_provisioner.drivers.node.maasdriver.models.base as model_base


class BootResource(model_base.ResourceBase):

    resource_url = 'boot-resources/{resource_id}/'
    fields = [
        'resource_id',
        'name',
        'type',
        'subarches',
        'architecture',
    ]
    json_fields = [
        'name',
        'type',
        'subarches',
        'architecture',
    ]

    def __init__(self, api_client, **kwargs):
        super().__init__(api_client, **kwargs)


class BootResources(model_base.ResourceCollectionBase):

    collection_url = 'boot-resources/'
    collection_resource = BootResource

    def __init__(self, api_client, **kwargs):
        super().__init__(api_client)

    def is_importing(self):
        """Check if boot resources are importing."""
        url = self.interpolate_url()

        self.logger.debug("Checking if boot resources are importing.")
        resp = self.api_client.get(url, op='is_importing')

        if resp.status_code == 200:
            resp_json = resp.json()
            self.logger.debug("Boot resource importing status: %s" % resp_json)
            return resp_json
        else:
            msg = "Error checking import status of boot resources: %s - %s" % (
                resp.status_code, resp.text)
            self.logger.error(msg)
            raise errors.DriverError(msg)

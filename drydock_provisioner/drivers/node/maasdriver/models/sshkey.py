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

class SshKey(model_base.ResourceBase):

    resource_url = 'account/prefs/sshkeys/{resource_id}/'
    fields = ['resource_id', 'key']
    json_fields = ['key']

    def __init__(self, api_client, **kwargs):
        super(SshKey, self).__init__(api_client, **kwargs)

        #Keys should never have newlines, but sometimes they get added
        self.key = self.key.replace("\n","")

class SshKeys(model_base.ResourceCollectionBase):

    collection_url = 'account/prefs/sshkeys/'
    collection_resource = SshKey

    def __init__(self, api_client, **kwargs):
        super(SshKeys, self).__init__(api_client)


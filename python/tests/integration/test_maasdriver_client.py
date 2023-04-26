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
import drydock_provisioner.config as config
import drydock_provisioner.drivers.node.maasdriver.api_client as client


class TestClass(object):

    def test_client_authenticate(self):
        client_config = config.DrydockConfig.node_driver['maasdriver']

        maas_client = client.MaasRequestFactory(client_config['api_url'],
                                                client_config['api_key'])

        resp = maas_client.get('account/',
                               params={'op': 'list_authorisation_tokens'})

        parsed = resp.json()

        assert len(parsed) > 0

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
import uuid

import drydock_provisioner.config as config
import drydock_provisioner.drivers.node.maasdriver.api_client as client
import drydock_provisioner.drivers.node.maasdriver.models.fabric as maas_fabric
import drydock_provisioner.drivers.node.maasdriver.models.subnet as maas_subnet

class TestClass(object):

    def test_maas_fabric(self):
         client_config = config.DrydockConfig.node_driver['maasdriver']

         maas_client = client.MaasRequestFactory(client_config['api_url'], client_config['api_key'])

         fabric_name = str(uuid.uuid4())

         fabric_list = maas_fabric.Fabrics(maas_client)
         fabric_list.refresh()

         test_fabric = maas_fabric.Fabric(maas_client, name=fabric_name, description='Test Fabric')
         test_fabric = fabric_list.add(test_fabric)

         assert test_fabric.name == fabric_name
         assert test_fabric.resource_id is not None

         query_fabric = maas_fabric.Fabric(maas_client, resource_id=test_fabric.resource_id)
         query_fabric.refresh()

         assert query_fabric.name == test_fabric.name

    def test_maas_subnet(self):
        client_config = config.DrydockConfig.node_driver['maasdriver']

        maas_client = client.MaasRequestFactory(client_config['api_url'], client_config['api_key'])

        subnet_list = maas_subnet.Subnets(maas_client)
        subnet_list.refresh()

        for s in subnet_list:
            print(s.to_dict())
        assert False




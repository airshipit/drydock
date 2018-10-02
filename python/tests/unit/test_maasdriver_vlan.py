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
'''Tests for the maasdriver node_results routine.'''
import pytest

from drydock_provisioner.drivers.node.maasdriver.models.vlan import Vlan
from drydock_provisioner.drivers.node.maasdriver.errors import RackControllerConflict


class TestMaasVlan():
    def test_add_rack_controller(self, mocker):
        '''Test vlan model method for setting a managing rack controller.'''

        # A object to return that looks like a requests response
        # object wrapping a MAAS API response
        class MockedResponse():

            status_code = 200

        vlan_fields = {'name': 'test', 'dhcp_on': True, 'mtu': 1500}

        primary_rack = "asdf79"
        secondary_rack = "asdf80"
        tertiary_rack = "asdf81"

        api_client = mocker.MagicMock()
        api_client.get.return_value = MockedResponse()

        vlan_obj = Vlan(api_client, **vlan_fields)

        vlan_obj.add_rack_controller(primary_rack)
        assert vlan_obj.primary_rack == primary_rack

        vlan_obj.add_rack_controller(secondary_rack)
        assert vlan_obj.secondary_rack == secondary_rack

        with pytest.raises(RackControllerConflict):
            vlan_obj.add_rack_controller(tertiary_rack)

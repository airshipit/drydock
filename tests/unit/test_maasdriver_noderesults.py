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
from drydock_provisioner.drivers.node.maasdriver.models.node_results import NodeResults


class TestMaasNodeResults():
    def test_get_noderesults(self, mocker):
        '''Test noderesults refresh call to load a list of NodeResults.'''
        # A object to return that looks like a requests response
        # object wrapping a MAAS API response
        class MockedResponse():

            status_code = 200

            def json(self):
                resp_content = [{
                    "id": 3,
                    "data": "SGVsbG8gV29ybGQh",
                    "result_type": 0,
                    "script_result": 0,
                    "resource_uri": "/MAAS/api/2.0/commissioning-scripts/",
                    "updated": "2018-07-06T14:32:20.129",
                    "node": {
                        "system_id": "r7mqnw"
                    },
                    "created": "2018-07-06T14:37:12.632",
                    "name": "hello_world"
                }]

                return resp_content

        api_client = mocker.MagicMock()
        api_client.get.return_value = MockedResponse()

        nr_list = NodeResults(api_client)
        nr_list.refresh()

        api_client.get.assert_called_with('commissioning-results/')
        assert len(nr_list) == 1

        nr = nr_list.singleton({'name': 'hello_world'})

        assert nr.get_decoded_data() == b'Hello World!'

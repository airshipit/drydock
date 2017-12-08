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
"""Test Validation API"""
from falcon import testing

import pytest
import json

from drydock_provisioner import policy
from drydock_provisioner.control.api import start_api

import falcon


class TestValidationApi(object):
    def test_post_validation_resp(self, input_files, falcontest):

        input_file = input_files.join("deckhand_fullsite.yaml")
        design_ref = "file://%s" % str(input_file)

        url = '/api/v1.0/validatedesign'
        hdr = {
            'Content-Type': 'application/json',
            'X-IDENTITY-STATUS': 'Confirmed',
            'X-USER-NAME': 'Test',
            'X-ROLES': 'admin'
        }
        body = {
            'rel': "design",
            'href': design_ref,
            'type': "application/x-yaml",
        }

        result = falcontest.simulate_post(
            url, headers=hdr, body=json.dumps(body))

        assert result.status == falcon.HTTP_200

    def test_href_error(self, input_files, falcontest):
        url = '/api/v1.0/validatedesign'
        hdr = {
            'Content-Type': 'application/json',
            'X-IDENTITY-STATUS': 'Confirmed',
            'X-USER-NAME': 'Test',
            'X-ROLES': 'admin'
        }
        body = {
            'rel': "design",
            'href': '',
            'type': "application/x-yaml",
        }

        result = falcontest.simulate_post(
            url, headers=hdr, body=json.dumps(body))

        assert result.status == falcon.HTTP_400

    def test_json_data_error(self, input_files, falcontest):
        url = '/api/v1.0/validatedesign'
        hdr = {
            'Content-Type': 'application/json',
            'X-IDENTITY-STATUS': 'Confirmed',
            'X-USER-NAME': 'Test',
            'X-ROLES': 'admin'
        }
        body = {}

        result = falcontest.simulate_post(
            url, headers=hdr, body=json.dumps(body))

        assert result.status == falcon.HTTP_400

    @pytest.fixture()
    def falcontest(self, drydock_state, deckhand_ingester,
                   deckhand_orchestrator):
        """Create a test harness for the the Falcon API framework."""
        policy.policy_engine = policy.DrydockPolicy()
        policy.policy_engine.register_policy()

        return testing.TestClient(
            start_api(
                state_manager=drydock_state,
                ingester=deckhand_ingester,
                orchestrator=deckhand_orchestrator))

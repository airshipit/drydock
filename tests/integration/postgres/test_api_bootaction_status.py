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
"""Generic testing for the orchestrator."""
from falcon import testing
import pytest
import os
import json

import ulid2
import falcon

import drydock_provisioner.objects.fields as hd_fields
from drydock_provisioner.control.api import start_api


class TestClass(object):
    def test_bootaction_detail(self, falcontest, seed_bootaction_status):
        """Test that the API allows boot action detail messages."""
        url = "/api/v1.0/bootactions/%s" % seed_bootaction_status['action_id']
        hdr = {
            'X-Bootaction-Key': "%s" % seed_bootaction_status['identity_key'],
            'Content-Type': 'application/json',
        }

        body = {
            'details': [
                {
                    'message': 'Test message.',
                    'error': True,
                },
            ]
        }

        result = falcontest.simulate_post(
            url, headers=hdr, body=json.dumps(body))

        assert result.status == falcon.HTTP_200

    def test_bootaction_status(self, falcontest, seed_bootaction_status):
        """Test that the API allows boot action status updates."""
        url = "/api/v1.0/bootactions/%s" % seed_bootaction_status['action_id']
        hdr = {
            'X-Bootaction-Key': "%s" % seed_bootaction_status['identity_key'],
            'Content-Type': 'application/json',
        }

        body = {
            'status': 'Success',
            'details': [
                {
                    'message': 'Test message.',
                    'error': True,
                },
            ]
        }

        result = falcontest.simulate_post(
            url, headers=hdr, body=json.dumps(body))

        assert result.status == falcon.HTTP_200

        result = falcontest.simulate_post(
            url, headers=hdr, body=json.dumps(body))

        assert result.status == falcon.HTTP_409

    def test_bootaction_schema(self, falcontest, seed_bootaction_status):
        """Test that the API allows boot action status updates."""
        url = "/api/v1.0/bootactions/%s" % seed_bootaction_status['action_id']
        hdr = {
            'X-Bootaction-Key': "%s" % seed_bootaction_status['identity_key'],
            'Content-Type': 'application/json',
        }

        body = {
            'foo': 'Success',
        }

        result = falcontest.simulate_post(
            url, headers=hdr, body=json.dumps(body))

        assert result.status == falcon.HTTP_400

    @pytest.fixture()
    def seed_bootaction_status(self, blank_state, yaml_orchestrator,
                               input_files):
        """Add a task and boot action to the database for testing."""
        input_file = input_files.join("fullsite.yaml")
        design_ref = "file://%s" % input_file
        test_task = yaml_orchestrator.create_task(
            action=hd_fields.OrchestratorAction.Noop, design_ref=design_ref)

        id_key = os.urandom(32)
        action_id = ulid2.generate_binary_ulid()
        blank_state.post_boot_action('compute01', test_task.get_id(), id_key,
                                     action_id, 'helloworld')

        ba = dict(
            nodename='compute01',
            task_id=test_task.get_id(),
            identity_key=id_key.hex(),
            action_id=ulid2.encode_ulid_base32(action_id))
        return ba

    @pytest.fixture()
    def falcontest(self, drydock_state, yaml_ingester, yaml_orchestrator):
        """Create a test harness for the the Falcon API framework."""
        return testing.TestClient(
            start_api(
                state_manager=drydock_state,
                ingester=yaml_ingester,
                orchestrator=yaml_orchestrator))

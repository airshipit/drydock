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
"""Test tasks API with Postgres backend."""
import pytest
from falcon import testing

import json

import drydock_provisioner.objects.fields as hd_fields
import drydock_provisioner.objects as objects

from drydock_provisioner import policy
from drydock_provisioner.control.api import start_api
from drydock_provisioner.control.base import DrydockRequestContext

import falcon


class TestTasksApi():
    def test_read_tasks(self, falcontest, blank_state):
        """Test that the tasks API responds with list of tasks."""
        url = '/api/v1.0/tasks'

        # TODO(sh8121att) Make fixture for request header forging
        hdr = {
            'Content-Type': 'application/json',
            'X-IDENTITY-STATUS': 'Confirmed',
            'X-USER-NAME': 'Test',
            'X-ROLES': 'admin'
        }

        resp = falcontest.simulate_get(url, headers=hdr)

        assert resp.status == falcon.HTTP_200

    def test_read_tasks_builddata(self, falcontest, blank_state,
                                  deckhand_orchestrator):
        """Test that the tasks API includes build data when prompted."""
        req_hdr = {
            'Content-Type': 'application/json',
            'X-IDENTITY-STATUS': 'Confirmed',
            'X-USER-NAME': 'Test',
            'X-ROLES': 'admin',
        }
        # Seed DB with a task
        ctx = DrydockRequestContext()
        task = deckhand_orchestrator.create_task(
            action=hd_fields.OrchestratorAction.PrepareNodes,
            design_ref='http://foo.com',
            context=ctx)

        # Seed DB with build data for task
        build_data = objects.BuildData(
            node_name='foo',
            task_id=task.get_id(),
            generator='hello_world',
            data_format='text/plain',
            data_element='Hello World!')
        blank_state.post_build_data(build_data)

        url = '/api/v1.0/tasks/%s' % str(task.get_id())

        resp = falcontest.simulate_get(
            url, headers=req_hdr, query_string="builddata=true")

        assert resp.status == falcon.HTTP_200

        resp_body = resp.json

        assert isinstance(resp_body.get('build_data'), list)

        assert len(resp_body.get('build_data')) == 1

    def test_create_task(self, falcontest, blank_state):
        url = '/api/v1.0/tasks'

        req_hdr = {
            'Content-Type': 'application/json',
            'X-IDENTITY-STATUS': 'Confirmed',
            'X-USER-NAME': 'Test',
            'X-ROLES': 'admin',
        }

        json_body = json.dumps({
            'action': 'verify_site',
            'design_ref': 'http://foo.com',
        })

        resp = falcontest.simulate_post(url, headers=req_hdr, body=json_body)

        assert resp.status == falcon.HTTP_201
        assert resp.headers.get('Location') is not None

    # TODO(sh8121att) Make this a general fixture in conftest.py
    @pytest.fixture()
    def falcontest(self, drydock_state, deckhand_ingester,
                   deckhand_orchestrator):
        """Create a test harness for the Falcon API framework."""
        policy.policy_engine = policy.DrydockPolicy()
        policy.policy_engine.register_policy()

        return testing.TestClient(
            start_api(
                state_manager=drydock_state,
                ingester=deckhand_ingester,
                orchestrator=deckhand_orchestrator))

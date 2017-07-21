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
import uuid
import logging
import json

from drydock_provisioner import policy
from drydock_provisioner.orchestrator import Orchestrator

from drydock_provisioner.control.base import DrydockRequestContext, BaseResource
from drydock_provisioner.control.tasks import TaskResource, TasksResource

import pytest
import falcon

logging.basicConfig(level=logging.DEBUG)

class TestTasksApi():

    def test_read_tasks(self, mocker):
        ''' DrydockPolicy.authorized() should correctly use oslo_policy to enforce
            RBAC policy based on a DrydockRequestContext instance
        '''

        mocker.patch('oslo_policy.policy.Enforcer')

        state = mocker.MagicMock()

        ctx = DrydockRequestContext()
        policy_engine = policy.DrydockPolicy()

        # Mock policy enforcement
        policy_mock_config = {'authorize.return_value': True}
        policy_engine.enforcer.configre_mock(**policy_mock_config)

        api = TasksResource(state_manager=state)

        # Configure context
        project_id = str(uuid.uuid4().hex)
        ctx.project_id = project_id
        user_id = str(uuid.uuid4().hex)
        ctx.user_id = user_id
        ctx.roles = ['admin']
        ctx.set_policy_engine(policy_engine)

        # Configure mocked request and response
        req = mocker.MagicMock()
        resp = mocker.MagicMock()
        req.context = ctx

        api.on_get(req, resp)

        expected_calls = [mocker.call.tasks]

        assert state.has_calls(expected_calls)
        assert resp.status == falcon.HTTP_200

    def test_create_task(self, mocker):
        mocker.patch('oslo_policy.policy.Enforcer')

        state = mocker.MagicMock()
        orch = mocker.MagicMock(spec=Orchestrator, wraps=Orchestrator(state_manager=state))
        orch_mock_config  = {'execute_task.return_value': True}
        orch.configure_mock(**orch_mock_config)

        ctx = DrydockRequestContext()
        policy_engine = policy.DrydockPolicy()

        json_body  = json.dumps({
                'action': 'verify_site',
                'design_id': 'foo',
            }).encode('utf-8')

        # Mock policy enforcement
        policy_mock_config = {'authorize.return_value': True}
        policy_engine.enforcer.configure_mock(**policy_mock_config)

        api = TasksResource(orchestrator=orch, state_manager=state)

        # Configure context
        project_id = str(uuid.uuid4().hex)
        ctx.project_id = project_id
        user_id = str(uuid.uuid4().hex)
        ctx.user_id = user_id
        ctx.roles = ['admin']
        ctx.set_policy_engine(policy_engine)

        # Configure mocked request and response
        req = mocker.MagicMock(spec=falcon.Request)
        req.content_type = 'application/json'
        req.stream.read.return_value = json_body
        resp = mocker.MagicMock(spec=falcon.Response)

        req.context = ctx

        api.on_post(req, resp)

        assert resp.status == falcon.HTTP_201
        assert resp.get_header('Location') is not None

    @policy.ApiEnforcer('physical_provisioner:read_task')
    def target_function(self, req, resp):
        return True

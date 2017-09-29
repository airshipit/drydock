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

from drydock_provisioner import policy
from drydock_provisioner.control.base import DrydockRequestContext

logging.basicConfig(level=logging.DEBUG)


class TestEnforcerDecorator():
    def test_apienforcer_decorator(self, mocker):
        ''' DrydockPolicy.authorized() should correctly use oslo_policy to enforce
            RBAC policy based on a DrydockRequestContext instance. authorized() is
            called via the policy.ApiEnforcer decorator.
        '''

        mocker.patch('oslo_policy.policy.Enforcer')

        ctx = DrydockRequestContext()
        policy_engine = policy.DrydockPolicy()

        # Configure context
        project_id = str(uuid.uuid4())
        ctx.project_id = project_id
        user_id = str(uuid.uuid4())
        ctx.user_id = user_id
        ctx.roles = ['admin']
        ctx.set_policy_engine(policy_engine)

        # Configure mocked request and response
        req = mocker.MagicMock()
        resp = mocker.MagicMock()
        req.context = ctx

        self.target_function(req, resp)

        expected_calls = [
            mocker.call.authorize(
                'physical_provisioner:read_task',
                {'project_id': project_id,
                 'user_id': user_id}, ctx.to_policy_view())
        ]

        policy_engine.enforcer.assert_has_calls(expected_calls)

    @policy.ApiEnforcer('physical_provisioner:read_task')
    def target_function(self, req, resp):
        return True

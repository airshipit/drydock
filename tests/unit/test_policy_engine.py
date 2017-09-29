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
from drydock_provisioner.policy import DrydockPolicy
from drydock_provisioner.control.base import DrydockRequestContext


class TestDefaultRules():
    def test_register_policy(self, mocker):
        ''' DrydockPolicy.register_policy() should correctly register all default
            policy rules
        '''

        mocker.patch('oslo_policy.policy.Enforcer')
        policy_engine = DrydockPolicy()
        policy_engine.register_policy()

        expected_calls = [
            mocker.call.register_defaults(DrydockPolicy.base_rules),
            mocker.call.register_defaults(DrydockPolicy.task_rules),
            mocker.call.register_defaults(DrydockPolicy.data_rules)
        ]

        # Validate the oslo_policy Enforcer was loaded with expected default policy rules
        policy_engine.enforcer.assert_has_calls(expected_calls, any_order=True)

    def test_authorize_context(self, mocker):
        ''' DrydockPolicy.authorized() should correctly use oslo_policy to enforce
            RBAC policy based on a DrydockRequestContext instance
        '''

        mocker.patch('oslo_policy.policy.Enforcer')
        ctx = DrydockRequestContext()

        # Configure context
        project_id = str(uuid.uuid4().hex)
        ctx.project_id = project_id
        user_id = str(uuid.uuid4().hex)
        ctx.user_id = user_id
        ctx.roles = ['admin']

        # Define action
        policy_action = 'physical_provisioner:read_task'

        policy_engine = DrydockPolicy()
        policy_engine.authorize(policy_action, ctx)

        expected_calls = [
            mocker.call.authorize(
                policy_action, {'project_id': project_id,
                                'user_id': user_id}, ctx.to_policy_view())
        ]

        policy_engine.enforcer.assert_has_calls(expected_calls)

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
"""Test Tasks API"""
from falcon import testing
from unittest.mock import Mock

import pytest
import json
import logging

from drydock_provisioner import policy
from drydock_provisioner.control.api import start_api
import drydock_provisioner.objects as objects
import drydock_provisioner.objects.fields as hd_fields

import falcon

LOG = logging.getLogger(__name__)


class TestTasksApiUnit(object):
    def test_get_tasks_id_resp(self, falcontest):
        url = '/api/v1.0/tasks/11111111-1111-1111-1111-111111111111'
        hdr = self.get_standard_header()

        result = falcontest.simulate_get(url, headers=hdr)

        assert result.status == falcon.HTTP_200
        response_json = json.loads(result.text)
        assert response_json[
            'task_id'] == '11111111-1111-1111-1111-111111111111'
        try:
            response_json['build_data']
            key_error = False
        except KeyError as ex:
            key_error = True
        assert key_error
        try:
            response_json['subtask_errors']
            key_error = False
        except KeyError as ex:
            key_error = True
        assert key_error

    def test_get_tasks_id_subtaskerror_noerrors_resp(self, falcontest):
        url = '/api/v1.0/tasks/11111111-1111-1111-1111-111111111111'
        hdr = self.get_standard_header()

        result = falcontest.simulate_get(
            url, headers=hdr, query_string='subtaskerrors=true')

        assert result.status == falcon.HTTP_200
        response_json = json.loads(result.text)
        assert response_json[
            'task_id'] == '11111111-1111-1111-1111-111111111111'
        assert response_json['subtask_errors'] == {}

    def test_get_tasks_id_subtaskerror_errors_resp(self, falcontest):
        url = '/api/v1.0/tasks/11111111-1111-1111-1111-111111111113'
        hdr = self.get_standard_header()

        result = falcontest.simulate_get(
            url, headers=hdr, query_string='subtaskerrors=true')

        assert result.status == falcon.HTTP_200
        response_json = json.loads(result.text)
        assert response_json[
            'task_id'] == '11111111-1111-1111-1111-111111111113'
        assert response_json['subtask_errors'][
            '11111111-1111-1111-1111-111111111116']['details'][
                'errorCount'] == 1

    def test_get_tasks_id_builddata_resp(self, falcontest):
        url = '/api/v1.0/tasks/11111111-1111-1111-1111-111111111111'
        hdr = self.get_standard_header()

        result = falcontest.simulate_get(
            url, headers=hdr, query_string='builddata=true')

        LOG.debug(result.text)
        assert result.status == falcon.HTTP_200
        response_json = json.loads(result.text)
        assert response_json['build_data']
        try:
            response_json['subtask_errors']
            key_error = False
        except KeyError as ex:
            key_error = True
        assert key_error

    def test_get_tasks_id_builddata_subtaskerrors_resp(self, falcontest):
        url = '/api/v1.0/tasks/11111111-1111-1111-1111-111111111111'
        hdr = self.get_standard_header()

        result = falcontest.simulate_get(
            url, headers=hdr, query_string='builddata=true&subtaskerrors=true')

        LOG.debug(result.text)
        assert result.status == falcon.HTTP_200
        response_json = json.loads(result.text)
        assert response_json['build_data']
        assert response_json['subtask_errors'] == {}

    def test_get_tasks_id_layers_resp(self, falcontest):
        url = '/api/v1.0/tasks/11111111-1111-1111-1111-111111111113'
        hdr = self.get_standard_header()

        result = falcontest.simulate_get(
            url, headers=hdr, query_string='layers=2')

        LOG.debug(result.text)
        assert result.status == falcon.HTTP_200
        response_json = json.loads(result.text)
        init_task_id = '11111111-1111-1111-1111-111111111113'
        sub_task_id_1 = '11111111-1111-1111-1111-111111111114'
        sub_task_id_2 = '11111111-1111-1111-1111-111111111115'
        assert response_json['init_task_id'] == init_task_id
        assert response_json[init_task_id]['task_id'] == init_task_id
        assert response_json[sub_task_id_1]['task_id'] == sub_task_id_1
        assert response_json[sub_task_id_2]['task_id'] == sub_task_id_2
        try:
            response_json['11111111-1111-1111-1111-111111111116']
            key_error = False
        except KeyError as ex:
            key_error = True
        assert key_error

    def test_get_tasks_id_layers_all_noerrors_resp(self, falcontest):
        url = '/api/v1.0/tasks/11111111-1111-1111-1111-111111111113'
        hdr = self.get_standard_header()

        result = falcontest.simulate_get(
            url, headers=hdr, query_string='layers=-1')

        LOG.debug(result.text)
        assert result.status == falcon.HTTP_200
        response_json = json.loads(result.text)
        init_task_id = '11111111-1111-1111-1111-111111111113'
        sub_task_id_1 = '11111111-1111-1111-1111-111111111114'
        sub_task_id_2 = '11111111-1111-1111-1111-111111111115'
        assert response_json['init_task_id'] == init_task_id
        assert response_json[init_task_id]['task_id'] == init_task_id
        assert response_json[sub_task_id_1]['task_id'] == sub_task_id_1
        assert response_json[sub_task_id_2]['task_id'] == sub_task_id_2
        try:
            response_json['11111111-1111-1111-1111-111111111116']
            key_error = False
        except KeyError as ex:
            key_error = True
        assert key_error is False
        try:
            response_json['subtask_errors']
            key_error = False
        except KeyError as ex:
            key_error = True
        assert key_error

    def test_get_tasks_id_layers_all_errors_resp(self, falcontest):
        url = '/api/v1.0/tasks/11111111-1111-1111-1111-111111111113'
        hdr = self.get_standard_header()

        result = falcontest.simulate_get(
            url, headers=hdr, query_string='layers=-1&subtaskerrors=true')

        LOG.debug(result.text)
        assert result.status == falcon.HTTP_200
        response_json = json.loads(result.text)
        init_task_id = '11111111-1111-1111-1111-111111111113'
        sub_task_id_1 = '11111111-1111-1111-1111-111111111114'
        sub_task_id_2 = '11111111-1111-1111-1111-111111111115'
        assert response_json['init_task_id'] == init_task_id
        assert response_json[init_task_id]['task_id'] == init_task_id
        assert response_json[sub_task_id_1]['task_id'] == sub_task_id_1
        assert response_json[sub_task_id_2]['task_id'] == sub_task_id_2
        try:
            response_json['11111111-1111-1111-1111-111111111116']
            key_error = False
        except KeyError as ex:
            key_error = True
        assert key_error is False
        assert response_json['subtask_errors'][
            '11111111-1111-1111-1111-111111111116']['details'][
                'errorCount'] == 1

    def test_input_not_found(self, falcontest):
        url = '/api/v1.0/tasks/11111111-1111-1111-1111-111111111112'
        hdr = self.get_standard_header()

        result = falcontest.simulate_get(url, headers=hdr)

        LOG.debug(result.text)
        assert result.status == falcon.HTTP_404

    @pytest.fixture()
    def falcontest(self, drydock_state, deckhand_ingester,
                   deckhand_orchestrator, mock_get_build_data, mock_get_task):
        """Create a test harness for the Falcon API framework."""
        policy.policy_engine = policy.DrydockPolicy()
        policy.policy_engine.register_policy()

        return testing.TestClient(
            start_api(
                state_manager=drydock_state,
                ingester=deckhand_ingester,
                orchestrator=deckhand_orchestrator))

    def get_standard_header(self):
        hdr = {
            'Content-Type': 'application/json',
            'X-IDENTITY-STATUS': 'Confirmed',
            'X-USER-NAME': 'Test',
            'X-ROLES': 'admin'
        }
        return hdr


@pytest.fixture()
def mock_get_task(drydock_state):
    def side_effect(*args):
        task_id = str(args[0])
        LOG.debug(task_id)
        # Basic task
        if task_id == '11111111-1111-1111-1111-111111111111':
            new_task = objects.Task()
            new_task.task_id = '11111111-1111-1111-1111-111111111111'
            new_task.result = objects.TaskStatus()
            new_task.result.set_status(hd_fields.ActionResult.Failure)
            new_task.result.add_status_msg(
                msg='Test', error=True, ctx_type='N/A', ctx='N/A')
            return new_task
        # Task not found
        if task_id == '11111111-1111-1111-1111-111111111112':
            return None
        # Task layers
        if task_id == '11111111-1111-1111-1111-111111111113':
            new_task = objects.Task()
            new_task.task_id = '11111111-1111-1111-1111-111111111113'
            new_task.subtask_id_list = [
                '11111111-1111-1111-1111-111111111114',
                '11111111-1111-1111-1111-111111111115'
            ]
            return new_task
        if task_id == '11111111-1111-1111-1111-111111111114':
            new_task = objects.Task()
            new_task.task_id = '11111111-1111-1111-1111-111111111114'
            return new_task
        if task_id == '11111111-1111-1111-1111-111111111115':
            new_task = objects.Task()
            new_task.task_id = '11111111-1111-1111-1111-111111111115'
            new_task.subtask_id_list = [
                '11111111-1111-1111-1111-111111111116',
                '11111111-1111-1111-1111-111111111117'
            ]
            return new_task
        if task_id == '11111111-1111-1111-1111-111111111116':
            new_task = objects.Task()
            new_task.task_id = '11111111-1111-1111-1111-111111111116'
            new_task.result = objects.TaskStatus()
            new_task.result.set_status(hd_fields.ActionResult.Failure)
            new_task.result.add_status_msg(
                msg='Test', error=True, ctx_type='N/A', ctx='N/A')
            LOG.debug('error_count')
            LOG.debug(new_task.result.error_count)
            return new_task
        LOG.debug('returning None')
        return None

    drydock_state.real_get_task = drydock_state.get_task
    drydock_state.get_task = Mock(side_effect=side_effect)

    yield
    drydock_state.get_task = Mock(wraps=None, side_effect=None)
    drydock_state.get_task = drydock_state.real_get_task

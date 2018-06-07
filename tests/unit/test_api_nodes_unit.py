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
"""Test Nodes API"""
from falcon import testing
from unittest.mock import Mock

import pytest
import json
import logging

from drydock_provisioner import policy
from drydock_provisioner.control.api import start_api
import drydock_provisioner.objects as objects

import falcon

LOG = logging.getLogger(__name__)


class TestNodesApiUnit(object):
    def test_post_nodes_resp(self, input_files, falcontest,
                             mock_process_node_filter):

        input_file = input_files.join("deckhand_fullsite.yaml")
        design_ref = "file://%s" % str(input_file)

        url = '/api/v1.0/nodefilter'
        hdr = self.get_standard_header()
        body = {
            'node_filter': 'filters',
            'design_ref': design_ref,
        }

        result = falcontest.simulate_post(
            url, headers=hdr, body=json.dumps(body))

        LOG.debug(result.text)
        assert result.status == falcon.HTTP_200
        assert result.text.count('n1') == 1
        assert result.text.count('n2') == 1

    def test_input_error(self, falcontest):
        url = '/api/v1.0/nodefilter'
        hdr = self.get_standard_header()
        body = {}

        result = falcontest.simulate_post(
            url, headers=hdr, body=json.dumps(body))

        LOG.debug(result.text)
        assert result.status == falcon.HTTP_400

    @pytest.fixture()
    def falcontest(self, drydock_state, deckhand_ingester,
                   deckhand_orchestrator, mock_get_build_data):
        """Create a test harness for the the Falcon API framework."""
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
def mock_process_node_filter(deckhand_orchestrator):
    def side_effect(**kwargs):
        n1 = objects.BaremetalNode()
        n1.name = 'n1'
        n1.site = 'test1'
        n2 = objects.BaremetalNode()
        n2.name = 'n2'
        n2.site = 'test2'
        return [n1, n2]

    deckhand_orchestrator.real_process_node_filter = deckhand_orchestrator.process_node_filter
    deckhand_orchestrator.process_node_filter = Mock(side_effect=side_effect)

    yield
    deckhand_orchestrator.process_node_filter = Mock(
        wraps=None, side_effect=None)
    deckhand_orchestrator.process_node_filter = deckhand_orchestrator.real_process_node_filter

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
import tarfile
import io
import falcon

import drydock_provisioner.objects.fields as hd_fields

from drydock_provisioner.control.api import start_api


class TestClass(object):
    def test_bootaction_context(self, falcontest, seed_bootaction):
        """Test that the API will return a boot action context"""
        url = "/api/v1.0/bootactions/nodes/%s/units" % seed_bootaction['nodename']
        auth_hdr = {'X-Bootaction-Key': "%s" % seed_bootaction['identity_key']}

        result = falcontest.simulate_get(url, headers=auth_hdr)

        assert result.status == falcon.HTTP_200

        fileobj = io.BytesIO(result.content)
        tarfile.open(mode='r:gz', fileobj=fileobj)

    def test_bootaction_context_notfound(self, falcontest):
        """Test that the API will return a 404 for unknown node"""
        url = "/api/v1.0/bootactions/nodes/%s/units" % 'foo'
        auth_hdr = {'X-Bootaction-Key': "%s" % 'bar'}

        result = falcontest.simulate_get(url, headers=auth_hdr)

        assert result.status == falcon.HTTP_404

    def test_bootaction_context_noauth(self, falcontest, seed_bootaction):
        """Test that the API will return a boot action context"""
        url = "/api/v1.0/bootactions/nodes/%s/units" % seed_bootaction['nodename']

        result = falcontest.simulate_get(url)

        assert result.status == falcon.HTTP_401

    def test_bootaction_context_badauth(self, falcontest, seed_bootaction):
        """Test that the API will return a boot action context"""
        url = "/api/v1.0/bootactions/nodes/%s/units" % seed_bootaction['nodename']
        auth_hdr = {'X-Bootaction-Key': 'deadbeef'}

        result = falcontest.simulate_get(url, headers=auth_hdr)

        assert result.status == falcon.HTTP_403

    @pytest.fixture()
    def seed_bootaction(self, blank_state, yaml_orchestrator, input_files,
                        mock_get_build_data):
        """Add a task and boot action to the database for testing."""
        input_file = input_files.join("fullsite.yaml")
        design_ref = "file://%s" % input_file
        test_task = yaml_orchestrator.create_task(
            action=hd_fields.OrchestratorAction.Noop, design_ref=design_ref)

        id_key = yaml_orchestrator.create_bootaction_context(
            'compute01', test_task)

        ba_ctx = dict(
            nodename='compute01',
            task_id=test_task.get_id(),
            identity_key=id_key.hex())
        return ba_ctx

    @pytest.fixture()
    def falcontest(self, drydock_state, yaml_ingester, yaml_orchestrator,
                   mock_get_build_data):
        """Create a test harness for the Falcon API framework."""
        return testing.TestClient(
            start_api(
                state_manager=drydock_state,
                ingester=yaml_ingester,
                orchestrator=yaml_orchestrator))

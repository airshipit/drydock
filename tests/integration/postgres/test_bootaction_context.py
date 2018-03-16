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
import pytest
import tarfile
import io
import falcon

from falcon import testing

import drydock_provisioner.objects.fields as hd_fields

from drydock_provisioner.control.api import start_api


class TestBootActionContext(object):
    def test_bootaction_context(self, falcontest, seed_bootaction_multinode):
        """Test that the API will return a boot action context"""
        for n, c in seed_bootaction_multinode.items():
            url = "/api/v1.0/bootactions/nodes/%s/units" % n
            auth_hdr = {'X-Bootaction-Key': "%s" % c['identity_key']}

            result = falcontest.simulate_get(url, headers=auth_hdr)

            assert result.status == falcon.HTTP_200

            fileobj = io.BytesIO(result.content)
            t = tarfile.open(mode='r:gz', fileobj=fileobj)
            t.close()

    @pytest.fixture()
    def seed_bootaction_multinode(self, blank_state, deckhand_orchestrator,
                                  input_files, mock_get_build_data):
        """Add a task and boot action to the database for testing."""
        input_file = input_files.join("deckhand_fullsite.yaml")
        design_ref = "file://%s" % input_file
        test_task = deckhand_orchestrator.create_task(
            action=hd_fields.OrchestratorAction.Noop, design_ref=design_ref)

        ba_ctx = dict()

        design_status, design_data = deckhand_orchestrator.get_effective_site(
            design_ref)

        for n in design_data.baremetal_nodes:
            id_key = deckhand_orchestrator.create_bootaction_context(
                n.name, test_task)
            node_ctx = dict(
                task_id=test_task.get_id(), identity_key=id_key.hex())
            ba_ctx[n.name] = node_ctx

        return ba_ctx

    @pytest.fixture()
    def falcontest(self, drydock_state, deckhand_ingester,
                   deckhand_orchestrator, mock_get_build_data):
        """Create a test harness for the the Falcon API framework."""
        return testing.TestClient(
            start_api(
                state_manager=drydock_state,
                ingester=deckhand_ingester,
                orchestrator=deckhand_orchestrator))

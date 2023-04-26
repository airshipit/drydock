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

import drydock_provisioner.objects.fields as hd_fields
from drydock_provisioner.orchestrator.orchestrator import Orchestrator
from drydock_provisioner.orchestrator.validations.validator import Validator


class TestDesignValidator(object):

    def test_validate_design(self, deckhand_ingester, drydock_state,
                             input_files, mock_get_build_data):
        """Test the basic validation engine."""

        input_file = input_files.join("deckhand_fullsite.yaml")
        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(state_manager=drydock_state,
                            ingester=deckhand_ingester)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        val = Validator(orch)
        response = val.validate_design(site_design)

        assert response.status == hd_fields.ValidationResult.Success

    def test_validate_no_nodes(self, deckhand_ingester, drydock_state,
                               input_files, mock_get_build_data):
        """Test that a design with no baremetal nodes validates."""

        input_file = input_files.join("deckhand_fullsite_no_nodes.yaml")
        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(state_manager=drydock_state,
                            ingester=deckhand_ingester)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        val = Validator(orch)
        response = val.validate_design(site_design)

        assert response.status == hd_fields.ValidationResult.Success

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
"""Test YAML data ingestion."""

from drydock_provisioner.statemgmt.state import DrydockState
import drydock_provisioner.objects as objects


class TestClass(object):
    def test_ingest_deckhand(self, input_files, setup, deckhand_ingester):
        input_file = input_files.join("deckhand_fullsite.yaml")

        design_state = DrydockState()
        design_ref = "file://%s" % str(input_file)

        design_status, design_data = deckhand_ingester.ingest_data(
            design_state=design_state, design_ref=design_ref)

        assert design_status.status == objects.fields.ValidationResult.Success
        assert len(design_data.host_profiles) == 2
        assert len(design_data.baremetal_nodes) == 3

    def test_ingest_deckhand_repos(self, input_files, setup, deckhand_ingester):
        """Test that the ingester properly parses repo definitions."""
        input_file = input_files.join("deckhand_fullsite.yaml")

        design_state = DrydockState()
        design_ref = "file://%s" % str(input_file)

        design_status, design_data = deckhand_ingester.ingest_data(
            design_state=design_state, design_ref=design_ref)

        assert design_status.status == objects.fields.ValidationResult.Success

        region_def = design_data.get_site()

        assert len(region_def.repositories) == 1
        assert region_def.repositories.remove_unlisted

        for r in region_def.repositories:
            assert 'docker' in r.url

    def test_ingest_deckhand_docref_exists(self, input_files, setup,
                                           deckhand_ingester):
        """Test that each processed document has a doc_ref."""
        input_file = input_files.join('deckhand_fullsite.yaml')

        design_state = DrydockState()
        design_ref = "file://%s" % str(input_file)
        design_status, design_data = deckhand_ingester.ingest_data(
            design_state=design_state, design_ref=design_ref)

        assert design_status.status == objects.fields.ValidationResult.Success
        for p in design_data.host_profiles:
            assert p.doc_ref is not None
            assert p.doc_ref.doc_schema == 'drydock/HostProfile/v1'
            assert p.doc_ref.doc_name is not None

    def test_ingest_yaml(self, input_files, setup, yaml_ingester):
        input_file = input_files.join("fullsite.yaml")

        design_state = DrydockState()
        design_ref = "file://%s" % str(input_file)

        design_status, design_data = yaml_ingester.ingest_data(
            design_state=design_state, design_ref=design_ref)

        assert design_status.status == objects.fields.ValidationResult.Success
        assert len(design_data.host_profiles) == 2
        assert len(design_data.baremetal_nodes) == 2

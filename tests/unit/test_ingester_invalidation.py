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
"""Test that boot action models are properly parsed."""
import logging

from drydock_provisioner.statemgmt.state import DrydockState
import drydock_provisioner.objects as objects

LOG = logging.getLogger(__name__)


class TestClass(object):
    def test_bootaction_parse(self, input_files, deckhand_ingester, setup):
        design_status, design_data = self.parse_design(
            "invalid_bootaction.yaml", input_files, deckhand_ingester)

        assert design_status.status == objects.fields.ActionResult.Failure

        error_msgs = [m for m in design_status.message_list if m.error]
        assert len(error_msgs) == 3

    def test_invalid_package_list(self, input_files, deckhand_ingester, setup):
        design_status, design_data = self.parse_design(
            "invalid_bootaction.yaml", input_files, deckhand_ingester)

        assert design_status.status == objects.fields.ActionResult.Failure

        pkg_list_bootaction = objects.DocumentReference(
            doc_type=objects.fields.DocumentType.Deckhand,
            doc_schema="drydock/BootAction/v1",
            doc_name="invalid_pkg_list")
        LOG.debug(design_status.to_dict())
        pkg_list_errors = [
            m for m in design_status.message_list
            if (m.error and pkg_list_bootaction in m.docs)
        ]

        assert len(pkg_list_errors) == 1

    def parse_design(self, filename, input_files, deckhand_ingester):
        input_file = input_files.join(filename)

        design_state = DrydockState()
        design_ref = "file://%s" % str(input_file)

        return deckhand_ingester.ingest_data(design_state, design_ref)

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
"""Test Validation Rule Rational Boot Storage"""

import logging

from drydock_provisioner.orchestrator.orchestrator import Orchestrator
from drydock_provisioner import objects
from drydock_provisioner.objects import fields as hd_fields
from drydock_provisioner.orchestrator.validations.bootaction_validity import BootactionDefined

LOG = logging.getLogger(__name__)


class TestBootactionsValidity(object):

    def test_valid_bootaction(self, deckhand_ingester, drydock_state, setup,
                              input_files, mock_get_build_data):
        input_file = input_files.join("validation.yaml")
        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(state_manager=drydock_state,
                            ingester=deckhand_ingester)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        assert status.status == hd_fields.ValidationResult.Success

        LOG.debug("%s" % status.to_dict())

        validator = BootactionDefined()
        message_list = validator.execute(site_design, orchestrator=orch)
        msg = message_list[0].to_dict()

        assert msg.get('error') is False
        assert msg.get('level') == hd_fields.MessageLevels.INFO
        assert len(message_list) == 1

    def test_absent_bootaction(self, deckhand_ingester, drydock_state, setup,
                               input_files, mock_get_build_data):
        input_file = input_files.join("absent_bootaction.yaml")
        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(state_manager=drydock_state,
                            ingester=deckhand_ingester)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        ba_msg = [
            msg for msg in status.message_list
            if ("DD4001" in msg.name
                and msg.level == hd_fields.MessageLevels.WARN)
        ]

        assert len(ba_msg) > 0

    def test_invalid_bootaction_pkg_list(self, deckhand_ingester,
                                         drydock_state, setup, input_files,
                                         mock_get_build_data):
        input_file = input_files.join("invalid_bootaction_pkg.yaml")
        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(state_manager=drydock_state,
                            ingester=deckhand_ingester)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        ba_doc = objects.DocumentReference(
            doc_type=hd_fields.DocumentType.Deckhand,
            doc_name="invalid_pkg_list",
            doc_schema="drydock/BootAction/v1")

        assert status.status == hd_fields.ValidationResult.Failure

        ba_msg = [msg for msg in status.message_list if ba_doc in msg.docs]

        assert len(ba_msg) > 0

        for msg in ba_msg:
            LOG.debug(msg)
            assert ":) is not a valid format" in msg.message
            assert msg.error

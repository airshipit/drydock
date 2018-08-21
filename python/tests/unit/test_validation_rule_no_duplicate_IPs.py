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

import re
import logging

from drydock_provisioner.orchestrator.validations.no_duplicate_ips_check import NoDuplicateIpsCheck
from drydock_provisioner.orchestrator.orchestrator import Orchestrator

LOG = logging.getLogger(__name__)


class TestDuplicateIPs(object):
    def test_no_duplicate_IPs(self, input_files, drydock_state,
                              deckhand_ingester):
        input_file = input_files.join("validation.yaml")
        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(
            state_manager=drydock_state, ingester=deckhand_ingester)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        validator = NoDuplicateIpsCheck()
        message_list = validator.execute(site_design, orchestrator=orch)
        msg = message_list[0].to_dict()

        assert msg.get('error') is False

    def test_no_duplicate_IPs_no_baremetal_node(
            self, input_files, drydock_state, deckhand_ingester):
        input_file = input_files.join("no_baremetal_node.yaml")
        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(
            state_manager=drydock_state, ingester=deckhand_ingester)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        validator = NoDuplicateIpsCheck()
        message_list = validator.execute(site_design, orchestrator=orch)
        msg = message_list[0].to_dict()

        assert 'No BaremetalNodes Found.' in msg.get('message')
        assert msg.get('error') is False

    def test_no_duplicate_IPs_no_addressing(self, input_files, drydock_state,
                                            deckhand_ingester):
        input_file = input_files.join("no_duplicate_IPs_no_addressing.yaml")
        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(
            state_manager=drydock_state, ingester=deckhand_ingester)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        validator = NoDuplicateIpsCheck()
        message_list = validator.execute(site_design, orchestrator=orch)
        msg = message_list[0].to_dict()

        assert 'No BaremetalNodes Found.' in msg.get('message')
        assert msg.get('error') is False

    def test_invalid_no_duplicate_IPs(self, input_files, drydock_state,
                                      deckhand_ingester):
        input_file = input_files.join("invalid_validation.yaml")
        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(
            state_manager=drydock_state, ingester=deckhand_ingester)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        validator = NoDuplicateIpsCheck()
        message_list = validator.execute(site_design)

        regex = re.compile('Duplicate IP Address Found: [0-9.]+')

        for msg in message_list:
            msg = msg.to_dict()
            LOG.debug(msg)
            assert len(msg.get('documents')) > 0
            assert msg.get('error') is True
            assert regex.search(msg.get('message')) is not None

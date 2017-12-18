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
"""Test Validation Rule Rational Network Bond"""

import re

from drydock_provisioner.orchestrator.orchestrator import Orchestrator
from drydock_provisioner.orchestrator.validations.validator import Validator


class TestRationalNetworkLinkBond(object):
    def test_rational_network_bond(self, mocker, deckhand_ingester,
                                   drydock_state, input_files):
        input_file = input_files.join("validation.yaml")
        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(
            state_manager=drydock_state, ingester=deckhand_ingester)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        message_list = Validator.rational_network_bond(site_design)
        msg = message_list[0].to_dict()

        assert msg.get('message') == 'Network Link Bonding'
        assert msg.get('error') is False
        assert len(message_list) == 1

    def test_invalid_rational_network_bond(self, mocker, deckhand_ingester,
                                           drydock_state, input_files):
        input_file = input_files.join("invalid_validation.yaml")

        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(
            state_manager=drydock_state, ingester=deckhand_ingester)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        message_list = Validator.rational_network_bond(site_design)

        regex = re.compile(
            'Network Link Bonding Error: Down delay is less than mon rate on BaremetalNode .+'
        )
        regex_1 = re.compile(
            'Network Link Bonding Error: Up delay is less than mon rate on BaremetalNode .+'
        )

        for msg in message_list:
            msg = msg.to_dict()
            assert msg.get('error') is True
            assert regex.match(
                msg.get('message')) is not None or regex_1.match(
                    msg.get('message')) is not None

        assert len(message_list) == 2

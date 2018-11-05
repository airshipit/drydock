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
import logging

from drydock_provisioner.orchestrator.orchestrator import Orchestrator
from drydock_provisioner.orchestrator.validations.rational_network_bond import RationalNetworkBond

LOG = logging.getLogger(__name__)


class TestRationalNetworkLinkBond(object):
    def test_rational_network_bond(self, mocker, deckhand_ingester,
                                   drydock_state, input_files):
        input_file = input_files.join("validation.yaml")
        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(
            state_manager=drydock_state, ingester=deckhand_ingester)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        validator = RationalNetworkBond()
        message_list = validator.execute(site_design, orchestrator=orch)
        msg = message_list[0].to_dict()

        assert msg.get('error') is False
        assert len(message_list) == 1
        assert len(msg.get('documents')) == 0

    def test_invalid_rational_network_bond(self, mocker, deckhand_ingester,
                                           drydock_state, input_files):
        input_file = input_files.join("invalid_validation.yaml")

        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(
            state_manager=drydock_state, ingester=deckhand_ingester)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        validator = RationalNetworkBond()
        message_list = validator.execute(site_design, orchestrator=orch)

        regex = re.compile(r'Down delay \S+ is less than mon rate \S+')
        regex_1 = re.compile(r'Up delay \S+ is less than mon rate \S+')

        for msg in message_list:
            msg = msg.to_dict()
            LOG.debug(msg)
            assert msg.get('error')
            assert len(msg.get('documents')) > 0
            assert any([
                regex.search(msg.get('message')),
                regex_1.search(msg.get('message'))
            ])

        assert len(message_list) == 2

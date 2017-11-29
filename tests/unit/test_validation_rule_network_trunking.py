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
"""Test Validation Rule Rational Network Trunking"""

from drydock_provisioner.orchestrator.orchestrator import Orchestrator
from drydock_provisioner.orchestrator.validations.validator import Validator


class TestRationalNetworkTrunking(object):
    def test_rational_network_trunking(
            self, deckhand_ingester, drydock_state, input_files):

        input_file = input_files.join("rational_network_trunking.yaml")
        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(state_manager=drydock_state, ingester=deckhand_ingester)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        message_list = Validator.network_trunking_rational(site_design)
        msg = message_list[0].to_dict()

        assert msg.get('message') == 'Rational Network Trunking'
        assert msg.get('error') is False

    def test_invalid_rational_network_trunking(
            self, deckhand_ingester, drydock_state, input_files):

        input_file = input_files.join("invalid_rational_network_trunking.yaml")
        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(state_manager=drydock_state, ingester=deckhand_ingester)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        message_list = Validator.network_trunking_rational(site_design)

        msg = message_list[0].to_dict()

        assert 'Rational Network Trunking Error: ' in msg.get('message')
        assert msg.get('error') is True

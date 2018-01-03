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

from drydock_provisioner.orchestrator.validations.validator import Validator
from drydock_provisioner.orchestrator.orchestrator import Orchestrator


class TestIPLocality(object):
    def test_ip_locality(self, input_files, drydock_state, deckhand_ingester):
        input_file = input_files.join("validation.yaml")
        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(state_manager=drydock_state, ingester=deckhand_ingester)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        message_list = Validator.ip_locality_check(site_design)
        msg = message_list[0].to_dict()

        assert msg.get('message') == 'IP Locality Success'
        assert msg.get('error') is False

    def test_ip_locality_no_networks(self, input_files, drydock_state, deckhand_ingester):
        input_file = input_files.join("ip_locality_no_networks.yaml")
        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(state_manager=drydock_state, ingester=deckhand_ingester)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        message_list = Validator.ip_locality_check(site_design)
        msg = message_list[0].to_dict()

        assert msg.get('message') == 'No networks found.'
        assert msg.get('error') is False

    def test_ip_locality_no_gateway(self, input_files, drydock_state, deckhand_ingester):
        input_file = input_files.join("ip_locality_no_gateway.yaml")
        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(state_manager=drydock_state, ingester=deckhand_ingester)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        message_list = Validator.ip_locality_check(site_design)
        msg = message_list[0].to_dict()

        assert 'No gateway found' in msg.get('message')
        assert msg.get('error') is True

    def test_no_baremetal_node(self, input_files, drydock_state, deckhand_ingester):
        input_file = input_files.join("no_baremetal_node.yaml")
        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(state_manager=drydock_state, ingester=deckhand_ingester)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        message_list = Validator.ip_locality_check(site_design)
        msg = message_list[0].to_dict()

        assert msg.get('message') == 'No baremetal_nodes found.'
        assert msg.get('error') is False

    def test_invalid_ip_locality_invalid_network(self, input_files, drydock_state, deckhand_ingester):
        input_file = input_files.join("invalid_validation.yaml")
        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(state_manager=drydock_state, ingester=deckhand_ingester)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        message_list = Validator.ip_locality_check(site_design)

        regex = re.compile('IP Locality Error: The gateway IP Address .+ is not within the defined CIDR: .+ of .+')
        regex_1 = re.compile('IP Locality Error: .+ is not a valid network.')
        regex_2 = re.compile('IP Locality Error: The IP Address .+ is not within the defined CIDR: .+ of .+ .')

        assert len(message_list) == 3
        for msg in message_list:
            msg = msg.to_dict()
            assert msg.get('error')
            assert (regex.match(msg.get('message')) is not None or
                    regex_1.match(msg.get('message')) is not None or
                    regex_2.match(msg.get('message')) is not None)

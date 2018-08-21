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

from drydock_provisioner.orchestrator.validations.ip_locality_check import IpLocalityCheck
from drydock_provisioner.orchestrator.orchestrator import Orchestrator

LOG = logging.getLogger(__name__)


class TestIPLocality(object):
    def test_ip_locality(self, input_files, drydock_state, deckhand_ingester):
        input_file = input_files.join("validation.yaml")
        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(
            state_manager=drydock_state, ingester=deckhand_ingester)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        validator = IpLocalityCheck()
        message_list = validator.execute(site_design, orchestrator=orch)
        msg = message_list[0].to_dict()

        assert msg.get('error') is False

    def test_ip_locality_no_networks(self, input_files, drydock_state,
                                     deckhand_ingester):
        input_file = input_files.join("ip_locality_no_networks.yaml")
        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(
            state_manager=drydock_state, ingester=deckhand_ingester)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        validator = IpLocalityCheck()
        message_list = validator.execute(site_design, orchestrator=orch)
        msg = message_list[0].to_dict()

        assert 'No networks found' in msg.get('message')
        assert msg.get('error') is False

    def test_ip_locality_no_gateway(self, input_files, drydock_state,
                                    deckhand_ingester):
        input_file = input_files.join("ip_locality_no_gateway.yaml")
        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(
            state_manager=drydock_state, ingester=deckhand_ingester)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        validator = IpLocalityCheck()
        message_list = validator.execute(site_design, orchestrator=orch)
        msg = message_list[0].to_dict()

        assert 'No gateway found' in msg.get('message')
        assert msg.get('error') is True

    def test_no_baremetal_node(self, input_files, drydock_state,
                               deckhand_ingester):
        input_file = input_files.join("no_baremetal_node.yaml")
        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(
            state_manager=drydock_state, ingester=deckhand_ingester)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        validator = IpLocalityCheck()
        message_list = validator.execute(site_design, orchestrator=orch)
        msg = message_list[0].to_dict()

        assert 'No baremetal_nodes found' in msg.get('message')
        assert msg.get('error') is False

    def test_invalid_ip_locality_invalid_network(
            self, input_files, drydock_state, deckhand_ingester):
        input_file = input_files.join("invalid_validation.yaml")
        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(
            state_manager=drydock_state, ingester=deckhand_ingester)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        validator = IpLocalityCheck()
        message_list = validator.execute(site_design, orchestrator=orch)

        regex = re.compile(
            'The gateway IP Address .+ is not within the defined CIDR: .+ of .+'
        )
        regex_1 = re.compile('.+ is not a valid network.')
        regex_2 = re.compile(
            'The IP Address .+ is not within the defined CIDR: .+ of .+ .')

        assert len(message_list) == 3

        for msg in message_list:
            msg = msg.to_dict()
            LOG.debug(msg)
            assert len(msg.get('documents')) > 0
            assert msg.get('error')
            assert any([
                regex.search(msg.get('message')),
                regex_1.search(msg.get('message')),
                regex_2.search(msg.get('message'))
            ])

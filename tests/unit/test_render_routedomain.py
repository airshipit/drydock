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

from drydock_provisioner.objects import fields as hd_fields
from drydock_provisioner.ingester.ingester import Ingester
from drydock_provisioner.statemgmt.state import DrydockState
from drydock_provisioner.orchestrator.orchestrator import Orchestrator


class TestRouteDomains(object):
    def test_routedomain_render(self, input_files, setup):
        input_file = input_files.join("deckhand_routedomain.yaml")

        design_state = DrydockState()
        design_ref = "file://%s" % str(input_file)

        ingester = Ingester()
        ingester.enable_plugin(
            'drydock_provisioner.ingester.plugins.deckhand.DeckhandIngester')

        orchestrator = Orchestrator(
            state_manager=design_state, ingester=ingester)

        design_status, design_data = orchestrator.get_effective_site(
            design_ref)

        assert design_status.status == hd_fields.ActionResult.Success

        net_rack3 = design_data.get_network('storage_rack3')

        route_cidrs = list()
        for r in net_rack3.routes:
            if 'subnet' in r and r.get('subnet') is not None:
                route_cidrs.append(r.get('subnet'))

        assert len(route_cidrs) == 3

        assert '172.16.1.0/24' in route_cidrs

        assert '172.16.2.0/24' in route_cidrs

        assert '172.16.3.0/24' in route_cidrs

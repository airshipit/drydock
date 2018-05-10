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
"""Test the node filter logic in the orchestrator."""

from drydock_provisioner.statemgmt.state import DrydockState
import drydock_provisioner.objects as objects


class TestClass(object):
    def test_node_filter_obj(self, input_files, setup, deckhand_orchestrator,
                             deckhand_ingester):
        input_file = input_files.join("deckhand_fullsite.yaml")

        design_state = DrydockState()
        design_ref = "file://%s" % str(input_file)

        design_status, design_data = deckhand_ingester.ingest_data(
            design_state=design_state, design_ref=design_ref)

        nf = objects.NodeFilter()
        nf.filter_type = 'intersection'
        nf.node_names = ['compute01']
        nfs = objects.NodeFilterSet(
            filter_set_type='intersection', filter_set=[nf])

        node_list = deckhand_orchestrator.process_node_filter(nfs, design_data)

        assert len(node_list) == 1

    def test_node_filter_dict(self, input_files, setup, deckhand_orchestrator,
                              deckhand_ingester):
        input_file = input_files.join("deckhand_fullsite.yaml")

        design_state = DrydockState()
        design_ref = "file://%s" % str(input_file)

        design_status, design_data = deckhand_ingester.ingest_data(
            design_state=design_state, design_ref=design_ref)

        nfs = {
            'filter_set_type':
            'intersection',
            'filter_set': [
                {
                    'filter_type': 'intersection',
                    'node_names': 'compute01',
                },
            ],
        }

        node_list = deckhand_orchestrator.process_node_filter(nfs, design_data)

        assert len(node_list) == 1

    def test_no_baremetal_nodes(self, input_files, setup, deckhand_orchestrator,
                                deckhand_ingester):
        input_file = input_files.join("deckhand_fullsite_no_nodes.yaml")

        design_state = DrydockState()
        design_ref = "file://%s" % str(input_file)

        design_status, design_data = deckhand_ingester.ingest_data(
            design_state=design_state, design_ref=design_ref)

        node_list = deckhand_orchestrator.process_node_filter(None, design_data)

        assert node_list == []

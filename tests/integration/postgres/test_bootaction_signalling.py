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
"""Test postgres integration for task management."""

from drydock_provisioner.objects import fields as hd_fields

class TestBootActionSignal(object):
    def test_bootaction_signal_disable(self, deckhand_orchestrator, drydock_state, input_files):
        """Test that disabled signaling omits a status entry in the DB."""
        input_file = input_files.join("deckhand_fullsite.yaml")
        design_ref = "file://%s" % str(input_file)

        task = deckhand_orchestrator.create_task(
            design_ref=design_ref,
            action=hd_fields.OrchestratorAction.Noop)

        deckhand_orchestrator.create_bootaction_context("compute01", task)

        # In the fullsite YAML, node 'compute01' is assigned two
        # bootactions - one with signaling enabled, one disabled.
        # Validate these counts

        bootactions = drydock_state.get_boot_actions_for_node('compute01')

        assert len(bootactions) == 1

        design_status, design_data = deckhand_orchestrator.get_effective_site(
            design_ref=design_ref)

        assert len(design_data.bootactions) == 2

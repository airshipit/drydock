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

    def test_bootaction_signal_disable(self, deckhand_orchestrator,
                                       drydock_state, input_files,
                                       mock_get_build_data):
        """Test that disabled signaling omits a status entry in the DB."""
        input_file = input_files.join("deckhand_fullsite.yaml")
        design_ref = "file://%s" % str(input_file)

        task = deckhand_orchestrator.create_task(
            design_ref=design_ref, action=hd_fields.OrchestratorAction.Noop)

        deckhand_orchestrator.create_bootaction_context("compute01", task)

        # In the fullsite YAML, node 'controller01' is assigned two
        # bootactions - one with signaling enabled, one disabled.
        # Validate these counts

        bootactions = drydock_state.get_boot_actions_for_node('compute01')

        assert len(bootactions) == 2

        # one bootaction should expecting signaling
        reported_bas = [
            x for x in bootactions.values()
            if x.get('action_status') == hd_fields.ActionResult.Incomplete
        ]
        assert len(reported_bas) == 1

        # one bootaction should not expect signaling
        unreported_bas = [
            x for x in bootactions.values()
            if not x.get('action_status') == hd_fields.ActionResult.Unreported
        ]
        assert len(unreported_bas) == 1

        design_status, design_data = deckhand_orchestrator.get_effective_site(
            design_ref=design_ref)

        assert len(design_data.bootactions) == 3

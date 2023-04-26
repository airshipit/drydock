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

import drydock_provisioner.objects as objects
import drydock_provisioner.objects.fields as hd_fields


class TestTaskFilterGeneration(object):

    def test_task_success_focus(self, setup):
        """Test that marking a task successful works correctly."""
        task = objects.Task(action=hd_fields.OrchestratorAction.Noop,
                            design_ref="http://foo.com")

        task.success(focus='foo')

        assert task.result.status == hd_fields.ActionResult.Success
        assert 'foo' in task.result.successes

    def test_task_failure_focus(self, setup):
        """Test that marking a task failed works correctly."""
        task = objects.Task(action=hd_fields.OrchestratorAction.Noop,
                            design_ref="http://foo.com")

        task.failure(focus='foo')

        assert task.result.status == hd_fields.ActionResult.Failure
        assert 'foo' in task.result.failures

    def test_task_success_nf(self, setup):
        """Test that a task can generate a node filter based on its success."""
        task = objects.Task(action=hd_fields.OrchestratorAction.Noop,
                            design_ref="http://foo.com")

        expected_nf = {
            'filter_set_type': 'intersection',
            'filter_set': [{
                'node_names': ['foo'],
                'filter_type': 'union',
            }]
        }

        task.success(focus='foo')

        nf = task.node_filter_from_successes()

        assert nf == expected_nf

    def test_task_failure_nf(self, setup):
        """Test that a task can generate a node filter based on its failure."""
        task = objects.Task(action=hd_fields.OrchestratorAction.Noop,
                            design_ref="http://foo.com")

        expected_nf = {
            'filter_set_type': 'intersection',
            'filter_set': [{
                'node_names': ['foo'],
                'filter_type': 'union',
            }]
        }

        task.failure(focus='foo')

        nf = task.node_filter_from_failures()

        assert nf == expected_nf

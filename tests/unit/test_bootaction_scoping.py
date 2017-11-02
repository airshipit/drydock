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

import drydock_provisioner.objects as objects


class TestClass(object):
    def test_bootaction_scoping_blankfilter(self, input_files,
                                            test_orchestrator):
        """Test a boot action with no node filter scopes correctly."""
        input_file = input_files.join("fullsite.yaml")

        design_ref = "file://%s" % str(input_file)

        design_status, design_data = test_orchestrator.get_effective_site(
            design_ref)

        assert design_status.status == objects.fields.ActionResult.Success

        assert len(design_data.bootactions) > 0

        for ba in design_data.bootactions:
            if ba.get_id() == 'helloworld':
                assert 'compute01' in ba.target_nodes
                assert 'controller01' in ba.target_nodes

    def test_bootaction_scoping_unionfilter(self, input_files,
                                            test_orchestrator):
        """Test a boot action with a union node filter scopes correctly."""
        input_file = input_files.join("fullsite.yaml")

        design_ref = "file://%s" % str(input_file)

        design_status, design_data = test_orchestrator.get_effective_site(
            design_ref)

        assert design_status.status == objects.fields.ActionResult.Success

        assert len(design_data.bootactions) > 0

        for ba in design_data.bootactions:
            if ba.get_id() == 'hw_filtered':
                assert 'compute01' in ba.target_nodes
                assert 'controller01' not in ba.target_nodes

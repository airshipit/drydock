# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
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
"""Test node model hostname and FQDN."""

import drydock_provisioner.objects as objects


class TestNodeNaming(object):
    def test_node_fqdn(self, deckhand_orchestrator, input_files, setup):
        """Test fqdn rendering."""
        input_file = input_files.join("deckhand_fullsite.yaml")

        design_ref = "file://%s" % str(input_file)

        design_status, design_data = deckhand_orchestrator.get_effective_site(
            design_ref)

        assert design_status.status == objects.fields.ValidationResult.Success

        # From the sample YAML, the domain assigned to the 'mgmt' network
        # is 'mgmt.sitename.example.com'. This is the primary network for
        # 'controller01'

        nodename = 'controller01'
        expected_fqdn = '{}.{}'.format(nodename, 'mgmt.sitename.example.com')

        node_model = design_data.get_baremetal_node(nodename)

        assert node_model

        assert node_model.get_fqdn(design_data) == expected_fqdn

    def test_node_domain(self, deckhand_orchestrator, input_files, setup):
        """Test domain rendering."""
        input_file = input_files.join("deckhand_fullsite.yaml")

        design_ref = "file://%s" % str(input_file)

        design_status, design_data = deckhand_orchestrator.get_effective_site(
            design_ref)

        assert design_status.status == objects.fields.ValidationResult.Success

        # From the sample YAML, the domain assigned to the 'mgmt' network
        # is 'mgmt.sitename.example.com'. This is the primary network for
        # 'controller01'

        node_name = 'controller01'
        expected_domain = 'mgmt.sitename.example.com'

        node_model = design_data.get_baremetal_node(node_name)

        assert node_model

        assert node_model.get_domain(design_data) == expected_domain

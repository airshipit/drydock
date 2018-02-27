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
"""Test Validation Rule Rational Boot Storage"""

import drydock_provisioner.config as config

from drydock_provisioner.orchestrator.orchestrator import Orchestrator
from drydock_provisioner.orchestrator.validations.platform_selection import PlatformSelection


class TestValidPlatform(object):
    def test_valid_platform(self, mocker, deckhand_ingester, drydock_state,
                            input_files, mock_get_build_data):
        mock_images = mocker.patch(
            "drydock_provisioner.drivers.node.maasdriver.driver."
            "MaasNodeDriver.get_available_images")
        mock_images.return_value = ['xenial']
        mock_kernels = mocker.patch(
            "drydock_provisioner.drivers.node.maasdriver.driver."
            "MaasNodeDriver.get_available_kernels")
        mock_kernels.return_value = ['ga-16.04', 'hwe-16.04']

        input_file = input_files.join("validation.yaml")
        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(
            state_manager=drydock_state,
            ingester=deckhand_ingester,
            enabled_drivers=config.config_mgr.conf.plugins)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        validator = PlatformSelection()
        results, message_list = validator.execute(
            site_design, orchestrator=orch)
        for r in results:
            print(r.to_dict())

        msg = results[0].to_dict()

        assert 'all nodes have valid' in msg.get('message')
        assert msg.get('error') is False
        assert len(results) == 1

    def test_invalid_platform(self, mocker, deckhand_ingester, drydock_state,
                              input_files):
        mock_images = mocker.patch(
            "drydock_provisioner.drivers.node.maasdriver.driver."
            "MaasNodeDriver.get_available_images")
        mock_images.return_value = ['xenial']
        mock_kernels = mocker.patch(
            "drydock_provisioner.drivers.node.maasdriver.driver."
            "MaasNodeDriver.get_available_kernels")
        mock_kernels.return_value = ['ga-16.04', 'hwe-16.04']

        input_file = input_files.join("invalid_kernel.yaml")
        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(
            state_manager=drydock_state,
            ingester=deckhand_ingester,
            enabled_drivers=config.config_mgr.conf.plugins)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        validator = PlatformSelection()
        results, message_list = validator.execute(
            site_design, orchestrator=orch)

        for r in results:
            print(r.to_dict())

        msg = results[0].to_dict()
        assert 'invalid kernel lts' in msg.get('message')
        assert msg.get('error')
        assert len(results) == 1

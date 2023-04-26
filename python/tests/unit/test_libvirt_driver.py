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
import logging

import libvirt
import pytest

from drydock_provisioner.error import DriverError
from drydock_provisioner.drivers.oob.libvirt_driver.actions.oob import LibvirtBaseAction

LOG = logging.getLogger(__name__)


class TestLibvirtOobDriver():

    def test_libvirt_init_session(self, mocker, deckhand_orchestrator,
                                  input_files, setup):
        """Test session initialization."""
        mocker.patch('libvirt.open')
        input_file = input_files.join("deckhand_fullsite_libvirt.yaml")

        design_ref = "file://%s" % str(input_file)

        design_status, design_data = deckhand_orchestrator.get_effective_site(
            design_ref)

        action = LibvirtBaseAction(None, None, None)

        # controller01 should have valid libvirt OOB description
        node = design_data.get_baremetal_node('controller01')

        LOG.debug("%s", str(node.obj_to_simple()))

        action.init_session(node)

        expected_calls = [mocker.call('qemu+ssh://dummy@somehost/system')]

        libvirt.open.assert_has_calls(expected_calls)

    def test_libvirt_invalid_uri(self, mocker, deckhand_orchestrator,
                                 input_files, setup):
        """Test session initialization."""
        mocker.patch('libvirt.open')
        input_file = input_files.join("deckhand_fullsite_libvirt.yaml")

        design_ref = "file://%s" % str(input_file)

        design_status, design_data = deckhand_orchestrator.get_effective_site(
            design_ref)

        action = LibvirtBaseAction(None, None, None)

        # compute01 should have invalid libvirt OOB description
        node = design_data.get_baremetal_node('compute01')

        LOG.debug("%s", str(node.obj_to_simple()))

        with pytest.raises(DriverError):
            action.init_session(node)

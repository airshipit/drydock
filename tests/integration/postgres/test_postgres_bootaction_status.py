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

import pytest
import os
import ulid2

from drydock_provisioner import objects


class TestPostgres(object):
    def test_bootaction_post(self, populateddb, drydock_state):
        """Test that a boot action status can be added."""
        id_key = os.urandom(32)
        action_id = ulid2.generate_binary_ulid()
        nodename = 'testnode'
        result = drydock_state.post_boot_action(nodename,
                                                populateddb.get_id(), id_key,
                                                action_id,
                                                'helloworld')

        assert result

    def test_bootaction_put(self, populateddb, drydock_state):
        """Test that a boot action status can be updated."""
        id_key = os.urandom(32)
        action_id = ulid2.generate_binary_ulid()
        nodename = 'testnode'
        drydock_state.post_boot_action(nodename,
                                       populateddb.get_id(), id_key, action_id, 'helloworld')

        result = drydock_state.put_bootaction_status(
            ulid2.encode_ulid_base32(action_id),
            action_status=objects.fields.ActionResult.Success)

        assert result

    def test_bootaction_get(self, populateddb, drydock_state):
        """Test that a boot action status can be retrieved."""
        id_key = os.urandom(32)
        action_id = ulid2.generate_binary_ulid()
        nodename = 'testnode'
        drydock_state.post_boot_action(nodename,
                                       populateddb.get_id(), id_key, action_id, 'helloworld')

        ba = drydock_state.get_boot_action(ulid2.encode_ulid_base32(action_id))

        assert ba.get('identity_key') == id_key

    @pytest.fixture(scope='function')
    def populateddb(self, blank_state):
        """Add dummy task to test against."""
        task = objects.Task(
            action='prepare_site', design_ref='http://test.com/design')

        blank_state.post_task(task)

        return task

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
"""Test postgres integration for build data management."""

import uuid
import copy

from datetime import datetime, timedelta

from drydock_provisioner import objects


class TestBuildData(object):

    def test_build_data_insert_no_collected_date(self, blank_state):
        """Test that build data can be inserted omitting collection date."""
        build_data_fields = {
            'node_name': 'foo',
            'generator': 'hello_world',
            'data_format': 'text/plain',
            'data_element': 'Hello World!',
            'task_id': uuid.uuid4(),
        }

        build_data = objects.BuildData(**build_data_fields)

        result = blank_state.post_build_data(build_data)

        assert result

    def test_build_data_insert_iwth_collected_date(self, blank_state):
        """Test that build data can be inserted specifying collection date."""
        build_data_fields = {
            'node_name': 'foo',
            'generator': 'hello_world',
            'data_format': 'text/plain',
            'data_element': 'Hello World!',
            'task_id': uuid.uuid4(),
            'collected_date': datetime.utcnow(),
        }

        build_data = objects.BuildData(**build_data_fields)

        result = blank_state.post_build_data(build_data)

        assert result

    def test_build_data_select(self, blank_state):
        """Test that build data can be deserialized from the database."""
        build_data_fields = {
            'node_name': 'foo',
            'generator': 'hello_world',
            'data_format': 'text/plain',
            'data_element': 'Hello World!',
            'task_id': uuid.uuid4(),
            'collected_date': datetime.utcnow(),
        }

        build_data = objects.BuildData(**build_data_fields)

        result = blank_state.post_build_data(build_data)

        assert result

        bd_list = blank_state.get_build_data()

        assert len(bd_list) == 1

        assert bd_list[0].to_dict() == build_data.to_dict()

    def test_build_data_select_latest(self, blank_state):
        """Test that build data can be selected for only latest instance."""
        build_data_latest = {
            'node_name': 'foo',
            'generator': 'hello_world',
            'data_format': 'text/plain',
            'data_element': 'Hello World!',
            'task_id': uuid.uuid4(),
            'collected_date': datetime.utcnow(),
        }

        build_data_old = copy.deepcopy(build_data_latest)
        build_data_old['collected_date'] = build_data_latest[
            'collected_date'] - timedelta(days=1)
        build_data_old['task_id'] = uuid.uuid4()

        build_data1 = objects.BuildData(**build_data_latest)
        build_data2 = objects.BuildData(**build_data_old)

        result = blank_state.post_build_data(build_data1)

        assert result

        result = blank_state.post_build_data(build_data2)

        assert result

        bd_list = blank_state.get_build_data(node_name='foo', latest=True)

        assert len(bd_list) == 1

        assert bd_list[0].to_dict() == build_data1.to_dict()

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

import uuid

from drydock_provisioner import objects

from drydock_provisioner.control.base import DrydockRequestContext


class TestPostgres(object):

    def test_task_insert(self, blank_state):
        """Test that a task can be inserted into the database."""
        ctx = DrydockRequestContext()
        ctx.user = 'sh8121'
        ctx.external_marker = str(uuid.uuid4())

        task = objects.Task(action='deploy_node',
                            design_ref='http://foo.bar/design',
                            context=ctx)

        result = blank_state.post_task(task)

        assert result

    def task_task_node_filter(self, blank_state):
        """Test that a persisted task persists node filter."""
        ctx = DrydockRequestContext()
        ctx.user = 'sh8121'
        ctx.external_marker = str(uuid.uuid4())

        node_filter = {
            'filter_set_type': 'union',
            'filter_set': [{
                'node_names': ['foo'],
                'filter_type': 'union'
            }]
        }
        task = objects.Task(action='deploy_node',
                            node_filter=node_filter,
                            design_ref='http://foo.bar/design',
                            context=ctx)

        result = blank_state.post_task(task)

        assert result

        saved_task = blank_state.get_task(task.get_id())

        assert saved_task.node_filter == node_filter

    def test_subtask_append(self, blank_state):
        """Test that the atomic subtask append method works."""

        task = objects.Task(action='deploy_node',
                            design_ref='http://foobar/design')
        subtask = objects.Task(action='deploy_node',
                               design_ref='http://foobar/design',
                               parent_task_id=task.task_id)

        blank_state.post_task(task)
        blank_state.post_task(subtask)
        blank_state.add_subtask(task.task_id, subtask.task_id)

        test_task = blank_state.get_task(task.task_id)

        assert subtask.task_id in test_task.subtask_id_list

    def test_task_select(self, populateddb, drydock_state):
        """Test that a task can be selected."""
        result = drydock_state.get_task(populateddb.task_id)

        assert result is not None
        assert result.design_ref == populateddb.design_ref

    def test_task_list(self, populateddb, drydock_state):
        """Test getting a list of all tasks."""

        result = drydock_state.get_tasks()

        assert len(result) == 1

    @pytest.fixture(scope='function')
    def populateddb(self, blank_state):
        """Add dummy task to test against."""
        task = objects.Task(action='prepare_site',
                            design_ref='http://test.com/design')

        blank_state.post_task(task)

        return task

import pytest

from drydock_provisioner import objects


class TestPostgres(object):
    def test_result_message_insert(self, populateddb, drydock_state):
        """Test that a result message for a task can be added."""
        msg1 = objects.TaskStatusMessage('Error 1', True, 'node', 'node1')
        msg2 = objects.TaskStatusMessage('Status 1', False, 'node', 'node1')

        result = drydock_state.post_result_message(populateddb.task_id, msg1)
        assert result
        result = drydock_state.post_result_message(populateddb.task_id, msg2)
        assert result

        task = drydock_state.get_task(populateddb.task_id)

        assert task.result.error_count == 1

        assert len(task.result.message_list) == 2

    @pytest.fixture(scope='function')
    def populateddb(self, blank_state):
        """Add dummy task to test against."""
        task = objects.Task(
            action='prepare_site', design_ref='http://test.com/design')

        blank_state.post_task(task)

        return task

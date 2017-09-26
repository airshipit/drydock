import pytest

import logging
import uuid
import time

from oslo_config import cfg

from sqlalchemy import sql
from sqlalchemy import create_engine

from drydock_provisioner import objects
import drydock_provisioner.config as config

from drydock_provisioner.control.base import DrydockRequestContext
from drydock_provisioner.statemgmt.state import DrydockState


class TestPostgres(object):

    def test_result_message_insert(self, populateddb, drydockstate):
        """Test that a result message for a task can be added."""
        msg1 = objects.TaskStatusMessage('Error 1', True, 'node', 'node1')
        msg2 = objects.TaskStatusMessage('Status 1', False, 'node', 'node1')

        result = drydockstate.post_result_message(populateddb.task_id, msg1)
        assert result
        result = drydockstate.post_result_message(populateddb.task_id, msg2)
        assert result

        task = drydockstate.get_task(populateddb.task_id)

        assert task.result.error_count == 1

        assert len(task.result.message_list) == 2

    @pytest.fixture(scope='function')
    def populateddb(self, cleandb):
        """Add dummy task to test against."""
        task = objects.Task(
            action='prepare_site', design_ref='http://test.com/design')

        q1 = sql.text('INSERT INTO tasks ' \
                      '(task_id, created, action, design_ref) ' \
                      'VALUES (:task_id, :created, :action, :design_ref)').execution_options(autocommit=True)

        engine = create_engine(
            config.config_mgr.conf.database.database_connect_string)
        conn = engine.connect()

        conn.execute(
            q1,
            task_id=task.task_id.bytes,
            created=task.created,
            action=task.action,
            design_ref=task.design_ref)

        conn.close()

        return task

    @pytest.fixture(scope='session')
    def drydockstate(self):
        return DrydockState()

    @pytest.fixture(scope='function')
    def cleandb(self, setup):
        q1 = sql.text('TRUNCATE TABLE tasks').execution_options(
            autocommit=True)
        q2 = sql.text('TRUNCATE TABLE result_message').execution_options(
            autocommit=True)
        q3 = sql.text('TRUNCATE TABLE active_instance').execution_options(
            autocommit=True)
        q4 = sql.text('TRUNCATE TABLE build_data').execution_options(
            autocommit=True)

        engine = create_engine(
            config.config_mgr.conf.database.database_connect_string)
        conn = engine.connect()

        conn.execute(q1)
        conn.execute(q2)
        conn.execute(q3)
        conn.execute(q4)

        conn.close()
        return

    @pytest.fixture(scope='module')
    def setup(self):
        objects.register_all()
        logging.basicConfig()

        req_opts = {
            'default': [cfg.IntOpt('leader_grace_period')],
            'database': [cfg.StrOpt('database_connect_string')],
            'logging': [
                cfg.StrOpt('global_logger_name', default='drydock'),
            ]
        }

        for k, v in req_opts.items():
            config.config_mgr.conf.register_opts(v, group=k)

        config.config_mgr.conf([])
        config.config_mgr.conf.set_override(
            name="database_connect_string",
            group="database",
            override=
            "postgresql+psycopg2://drydock:drydock@localhost:5432/drydock")
        config.config_mgr.conf.set_override(
            name="leader_grace_period", group="default", override=15)

        return

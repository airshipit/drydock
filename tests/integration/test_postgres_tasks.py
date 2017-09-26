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
    def test_task_insert(self, cleandb, drydockstate):
        """Test that a task can be inserted into the database."""
        ctx = DrydockRequestContext()
        ctx.user = 'sh8121'
        ctx.external_marker = str(uuid.uuid4())

        task = objects.Task(
            action='deploy_node',
            design_ref='http://foo.bar/design',
            context=ctx)

        result = drydockstate.post_task(task)

        assert result == True

    def test_subtask_append(self, cleandb, drydockstate):
        """Test that the atomic subtask append method works."""

        task = objects.Task(action='deploy_node', design_ref='http://foobar/design')
        subtask = objects.Task(action='deploy_node', design_ref='http://foobar/design', parent_task_id=task.task_id)

        drydockstate.post_task(task)
        drydockstate.post_task(subtask)
        drydockstate.add_subtask(task.task_id, subtask.task_id)

        test_task = drydockstate.get_task(task.task_id)

        assert subtask.task_id in test_task.subtask_id_list

    def test_task_select(self, populateddb, drydockstate):
        """Test that a task can be selected."""
        result = drydockstate.get_task(populateddb.task_id)

        assert result is not None
        assert result.design_ref == populateddb.design_ref

    def test_task_list(self, populateddb, drydockstate):
        """Test getting a list of all tasks."""

        result = drydockstate.get_tasks()

        assert len(result) == 1

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

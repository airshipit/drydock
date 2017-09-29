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
"""Access methods for managing external data access and persistence."""

import logging
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy import sql
from sqlalchemy import MetaData

import drydock_provisioner.objects as objects
import drydock_provisioner.objects.fields as hd_fields

from .db import tables
from .design import resolver

from drydock_provisioner import config

from drydock_provisioner.error import StateError


class DrydockState(object):
    def __init__(self):
        self.logger = logging.getLogger(
            config.config_mgr.conf.logging.global_logger_name)

        self.resolver = resolver.DesignResolver()
        return

    def connect_db(self):
        """Connect the state manager to the persistent DB."""
        self.db_engine = create_engine(
            config.config_mgr.conf.database.database_connect_string)
        self.db_metadata = MetaData(bind=self.db_engine)

        self.tasks_tbl = tables.Tasks(self.db_metadata)
        self.result_message_tbl = tables.ResultMessage(self.db_metadata)
        self.active_instance_tbl = tables.ActiveInstance(self.db_metadata)
        self.build_data_tbl = tables.BuildData(self.db_metadata)
        return

    def tabularasa(self):
        """Truncate all tables.

        Used for testing to truncate all tables so the database is clean.
        """
        table_names = [
            'tasks',
            'result_message',
            'active_instance',
            'build_data',
        ]

        conn = self.db_engine.connect()
        for t in table_names:
            query_text = sql.text(
                "TRUNCATE TABLE %s" % t).execution_options(autocommit=True)
            conn.execute(query_text)
        conn.close()

    def get_design_documents(self, design_ref):
        return self.resolver.resolve_reference(design_ref)

    def get_tasks(self):
        """Get all tasks in the database."""
        try:
            conn = self.db_engine.connect()
            query = sql.select([self.tasks_tbl])
            rs = conn.execute(query)

            task_list = [objects.Task.from_db(dict(r)) for r in rs]

            self._assemble_tasks(task_list=task_list)

            # add reference to this state manager to each task
            for t in task_list:
                t.statemgr = self

            conn.close()

            return task_list
        except Exception as ex:
            self.logger.error("Error querying task list: %s" % str(ex))
            return []

    def get_complete_subtasks(self, task_id):
        """Query database for subtasks of the provided task that are complete.

        Complete is defined as status of Terminated or Complete.

        :param task_id: uuid.UUID ID of the parent task for subtasks
        """
        try:
            conn = self.db_engine.connect()
            query_text = sql.text(
                "SELECT * FROM tasks WHERE "  # nosec no strings are user-sourced
                "parent_task_id = :parent_task_id AND "
                "status IN ('" + hd_fields.TaskStatus.Terminated + "','" +
                hd_fields.TaskStatus.Complete + "')")

            rs = conn.execute(query_text, parent_task_id=task_id.bytes)
            task_list = [objects.Task.from_db(dict(r)) for r in rs]
            conn.close()

            self._assemble_tasks(task_list=task_list)
            for t in task_list:
                t.statemgr = self

            return task_list
        except Exception as ex:
            self.logger.error("Error querying complete subtask: %s" % str(ex))
            return []

    def get_active_subtasks(self, task_id):
        """Query database for subtasks of the provided task that are active.

        Active is defined as status of not Terminated or Complete. Returns
        list of objects.Task instances

        :param task_id: uuid.UUID ID of the parent task for subtasks
        """
        try:
            conn = self.db_engine.connect()
            query_text = sql.text(
                "SELECT * FROM tasks WHERE "  # nosec no strings are user-sourced
                "parent_task_id = :parent_task_id AND "
                "status NOT IN ['" + hd_fields.TaskStatus.Terminated + "','" +
                hd_fields.TaskStatus.Complete + "']")

            rs = conn.execute(query_text, parent_task_id=task_id.bytes)

            task_list = [objects.Task.from_db(dict(r)) for r in rs]
            conn.close()

            self._assemble_tasks(task_list=task_list)

            for t in task_list:
                t.statemgr = self

            return task_list
        except Exception as ex:
            self.logger.error("Error querying active subtask: %s" % str(ex))
            return []

    def get_next_queued_task(self, allowed_actions=None):
        """Query the database for the next (by creation timestamp) queued task.

        If specified, only select tasks for one of the actions in the allowed_actions
        list.

        :param allowed_actions: list of string action names
        """
        try:
            conn = self.db_engine.connect()
            if allowed_actions is None:
                query = self.tasks_tbl.select().where(
                    self.tasks_tbl.c.status ==
                    hd_fields.TaskStatus.Queued).order_by(
                        self.tasks_tbl.c.created.asc())
                rs = conn.execute(query)
            else:
                query = sql.text("SELECT * FROM tasks WHERE "
                                 "status = :queued_status AND "
                                 "action = ANY(:actions) "
                                 "ORDER BY created ASC")
                rs = conn.execute(
                    query,
                    queued_status=hd_fields.TaskStatus.Queued,
                    actions=allowed_actions)

            r = rs.first()
            conn.close()

            if r is not None:
                task = objects.Task.from_db(dict(r))
                self._assemble_tasks(task_list=[task])
                task.statemgr = self
                return task
            else:
                return None
        except Exception as ex:
            self.logger.error(
                "Error querying for next queued task: %s" % str(ex),
                exc_info=True)
            return None

    def get_task(self, task_id):
        """Query database for task matching task_id.

        :param task_id: uuid.UUID of a task_id to query against
        """
        try:
            conn = self.db_engine.connect()
            query = self.tasks_tbl.select().where(
                self.tasks_tbl.c.task_id == task_id.bytes)
            rs = conn.execute(query)

            r = rs.fetchone()

            task = objects.Task.from_db(dict(r))

            self.logger.debug(
                "Assembling result messages for task %s." % str(task.task_id))
            self._assemble_tasks(task_list=[task])
            task.statemgr = self

            conn.close()

            return task

        except Exception as ex:
            self.logger.error(
                "Error querying task %s: %s" % (str(task_id), str(ex)),
                exc_info=True)
            return None

    def post_result_message(self, task_id, msg):
        """Add a result message to database attached to task task_id.

        :param task_id: uuid.UUID ID of the task the msg belongs to
        :param msg: instance of objects.TaskStatusMessage
        """
        try:
            conn = self.db_engine.connect()
            query = self.result_message_tbl.insert().values(
                task_id=task_id.bytes, **(msg.to_db()))
            conn.execute(query)
            conn.close()
            return True
        except Exception as ex:
            self.logger.error(
                "Error inserting result message for task %s: %s" %
                (str(task_id), str(ex)))
            return False

    def _assemble_tasks(self, task_list=None):
        """Attach all the appropriate result messages to the tasks in the list.

        :param task_list: a list of objects.Task instances to attach result messages to
        """
        if task_list is None:
            return None

        conn = self.db_engine.connect()
        query = sql.select([
            self.result_message_tbl
        ]).where(self.result_message_tbl.c.task_id == sql.bindparam(
            'task_id')).order_by(self.result_message_tbl.c.sequence.asc())
        query.compile(self.db_engine)

        for t in task_list:
            rs = conn.execute(query, task_id=t.task_id.bytes)
            error_count = 0
            for r in rs:
                msg = objects.TaskStatusMessage.from_db(dict(r))
                if msg.error:
                    error_count = error_count + 1
                t.result.message_list.append(msg)
            t.result.error_count = error_count

        conn.close()

    def post_task(self, task):
        """Insert a task into the database.

        Does not insert attached result messages

        :param task: instance of objects.Task to insert into the database.
        """
        try:
            conn = self.db_engine.connect()
            query = self.tasks_tbl.insert().values(
                **(task.to_db(include_id=True)))
            conn.execute(query)
            conn.close()
            return True
        except Exception as ex:
            self.logger.error("Error inserting task %s: %s" %
                              (str(task.task_id), str(ex)))
            return False

    def put_task(self, task):
        """Update a task in the database.

        :param task: objects.Task instance to reference for update values
        """
        try:
            conn = self.db_engine.connect()
            query = self.tasks_tbl.update().where(
                self.tasks_tbl.c.task_id == task.task_id.bytes).values(
                    **(task.to_db(include_id=False)))
            rs = conn.execute(query)
            if rs.rowcount == 1:
                conn.close()
                return True
            else:
                conn.close()
                return False
        except Exception as ex:
            self.logger.error("Error updating task %s: %s" %
                              (str(task.task_id), str(ex)))
            return False

    def add_subtask(self, task_id, subtask_id):
        """Add new task to subtask list.

        :param task_id: uuid.UUID parent task ID
        :param subtask_id: uuid.UUID new subtask ID
        """
        query_string = sql.text(
            "UPDATE tasks "
            "SET subtask_id_list = array_append(subtask_id_list, :new_subtask) "
            "WHERE task_id = :task_id").execution_options(autocommit=True)

        try:
            conn = self.db_engine.connect()
            rs = conn.execute(
                query_string,
                new_subtask=subtask_id.bytes,
                task_id=task_id.bytes)
            rc = rs.rowcount
            conn.close()
            if rc == 1:
                return True
            else:
                return False
        except Exception as ex:
            self.logger.error("Error appending subtask %s to task %s: %s" %
                              (str(subtask_id), str(task_id), str(ex)))
            return False

    def maintain_leadership(self, leader_id):
        """The active leader reaffirms its existence.

        :param leader_id: uuid.UUID ID of the leader
        """
        try:
            conn = self.db_engine.connect()
            query = self.active_instance_tbl.update().where(
                self.active_instance_tbl.c.identity == leader_id.bytes).values(
                    last_ping=datetime.utcnow())
            rs = conn.execute(query)
            rc = rs.rowcount
            conn.close()

            if rc == 1:
                return True
            else:
                return False
        except Exception as ex:
            self.logger.error("Error maintaining leadership: %s" % str(ex))

    def claim_leadership(self, leader_id):
        """Claim active instance status for leader_id.

        Attempt to claim leadership for leader_id. If another leader_id already has leadership
        and has checked-in within the configured interval, this claim fails. If the last check-in
        of an active instance is outside the configured interval, this claim will overwrite the
        current active instance and succeed. If leadership has not been claimed, this call will
        succeed.

        All leadership claims by an instance should use the same leader_id

        :param leader_id: a uuid.UUID instance identifying the instance to be considered active
        """
        query_string = sql.text(  # nosec no strings are user-sourced
            "INSERT INTO active_instance (dummy_key, identity, last_ping) "
            "VALUES (1, :instance_id, timezone('UTC', now())) "
            "ON CONFLICT (dummy_key) DO UPDATE SET "
            "identity = :instance_id "
            "WHERE active_instance.last_ping < (now() - interval '%d seconds')"
            % (config.config_mgr.conf.leader_grace_period
               )).execution_options(autocommit=True)

        try:
            conn = self.db_engine.connect()
            conn.execute(query_string, instance_id=leader_id.bytes)
            check_query = self.active_instance_tbl.select().where(
                self.active_instance_tbl.c.identity == leader_id.bytes)
            rs = conn.execute(check_query)
            r = rs.fetchone()
            conn.close()
            if r is not None:
                return True
            else:
                return False
        except Exception as ex:
            self.logger.error("Error executing leadership claim: %s" % str(ex))
            return False

    def abdicate_leadership(self, leader_id):
        """Give up leadership for ``leader_id``.

        :param leader_id: a uuid.UUID instance identifying the instance giving up leadership
        """
        try:
            conn = self.db_engine.connect()
            query = self.active_instance_tbl.delete().where(
                self.active_instance_tbl.c.identity == leader_id.bytes)
            rs = conn.execute(query)
            rc = rs.rowcount
            conn.close()

            if rc == 1:
                return True
            else:
                return False
        except Exception as ex:
            self.logger.error("Error abidcating leadership: %s" % str(ex))

    def post_promenade_part(self, part):
        my_lock = self.promenade_lock.acquire(blocking=True, timeout=10)
        if my_lock:
            if self.promenade.get(part.target, None) is not None:
                self.promenade[part.target].append(part.obj_to_primitive())
            else:
                self.promenade[part.target] = [part.obj_to_primitive()]
            self.promenade_lock.release()
            return None
        else:
            raise StateError("Could not acquire lock")

    def get_promenade_parts(self, target):
        parts = self.promenade.get(target, None)

        if parts is not None:
            return [
                objects.PromenadeConfig.obj_from_primitive(p) for p in parts
            ]
        else:
            # Return an empty list just to play nice with extend
            return []

    def set_bootdata_key(self, hostname, design_id, data_key):
        my_lock = self.bootdata_lock.acquire(blocking=True, timeout=10)
        if my_lock:
            self.bootdata[hostname] = {'design_id': design_id, 'key': data_key}
            self.bootdata_lock.release()
            return None
        else:
            raise StateError("Could not acquire lock")

    def get_bootdata_key(self, hostname):
        return self.bootdata.get(hostname, None)

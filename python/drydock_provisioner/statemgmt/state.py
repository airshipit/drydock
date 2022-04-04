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
import uuid
from datetime import datetime
import ulid2

from sqlalchemy import create_engine
from sqlalchemy import sql
from sqlalchemy import MetaData

import drydock_provisioner.objects as objects
import drydock_provisioner.objects.fields as hd_fields
import drydock_provisioner.error as errors

from .db import tables

from drydock_provisioner import config
from .design.resolver import ReferenceResolver


class DrydockState(object):
    def __init__(self):
        self.logger = logging.getLogger(
            config.config_mgr.conf.logging.global_logger_name)

        return

    def connect_db(self):
        """Connect the state manager to the persistent DB."""
        self.db_engine = create_engine(
            config.config_mgr.conf.database.database_connect_string,
            pool_size=config.config_mgr.conf.database.pool_size,
            pool_pre_ping=config.config_mgr.conf.database.pool_pre_ping,
            max_overflow=config.config_mgr.conf.database.pool_overflow,
            pool_timeout=config.config_mgr.conf.database.pool_timeout,
            pool_recycle=config.config_mgr.conf.database.connection_recycle)
        self.db_metadata = MetaData(bind=self.db_engine)

        self.tasks_tbl = tables.Tasks(self.db_metadata)
        self.result_message_tbl = tables.ResultMessage(self.db_metadata)
        self.active_instance_tbl = tables.ActiveInstance(self.db_metadata)
        self.boot_action_tbl = tables.BootAction(self.db_metadata)
        self.ba_status_tbl = tables.BootActionStatus(self.db_metadata)
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
            'boot_action',
            'boot_action_status',
            'build_data',
        ]

        with self.db_engine.connect() as conn:
            for t in table_names:
                query_text = sql.text(
                    "TRUNCATE TABLE %s" % t).execution_options(autocommit=True)
                conn.execute(query_text)

    def get_design_documents(self, design_ref):
        return ReferenceResolver.resolve_reference(design_ref)

    def get_tasks(self):
        """Get all tasks in the database."""
        try:
            with self.db_engine.connect() as conn:
                query = sql.select([self.tasks_tbl])
                rs = conn.execute(query)

                task_list = [objects.Task.from_db(dict(r)) for r in rs]

                self._assemble_tasks(task_list=task_list)

                # add reference to this state manager to each task
                for t in task_list:
                    t.statemgr = self

            return task_list
        except Exception as ex:
            self.logger.error("Error querying task list: %s" % str(ex))
            return []

    def get_complete_subtasks(self, task_id):
        """Query database for subtasks of the provided task that are complete.

        Complete is defined as status of Terminated or Complete.

        :param task_id: uuid.UUID ID of the parent task for subtasks
        """
        query_text = sql.text(
            "SELECT * FROM tasks WHERE "  # nosec no strings are user-sourced
            "parent_task_id = :parent_task_id AND status "
            "IN ('" + hd_fields.TaskStatus.Terminated + "','"
            + hd_fields.TaskStatus.Complete + "')")
        return self._query_subtasks(task_id, query_text,
                                    "Error querying complete subtask: %s")

    def get_active_subtasks(self, task_id):
        """Query database for subtasks of the provided task that are active.

        Active is defined as status of not Terminated or Complete. Returns
        list of objects.Task instances

        :param task_id: uuid.UUID ID of the parent task for subtasks
        """
        query_text = sql.text(
            "SELECT * FROM tasks WHERE "  # nosec no strings are user-sourced
            "parent_task_id = :parent_task_id AND status "
            "NOT IN ['" + hd_fields.TaskStatus.Terminated + "','"
            + hd_fields.TaskStatus.Complete + "']")
        return self._query_subtasks(task_id, query_text,
                                    "Error querying active subtask: %s")

    def get_all_subtasks(self, task_id):
        """Query database for all subtasks of the provided task.

        :param task_id: uuid.UUID ID of the parent task for subtasks
        """
        query_text = sql.text(
            "SELECT * FROM tasks WHERE "  # nosec no strings are user-sourced
            "parent_task_id = :parent_task_id")
        return self._query_subtasks(task_id, query_text,
                                    "Error querying all subtask: %s")

    def _query_subtasks(self, task_id, query_text, error):
        try:
            with self.db_engine.connect() as conn:
                rs = conn.execute(query_text, parent_task_id=task_id.bytes)
                task_list = [objects.Task.from_db(dict(r)) for r in rs]

                self._assemble_tasks(task_list=task_list)
                for t in task_list:
                    t.statemgr = self
                return task_list
        except Exception as ex:
            self.logger.error(error % str(ex))
            return []

    def get_next_queued_task(self, allowed_actions=None):
        """Query the database for the next (by creation timestamp) queued task.

        If specified, only select tasks for one of the actions in the allowed_actions
        list.

        :param allowed_actions: list of string action names
        """
        try:
            with self.db_engine.connect() as conn:
                if allowed_actions is None:
                    query = self.tasks_tbl.select().where(
                        self.tasks_tbl.c.status == hd_fields.TaskStatus.
                        Queued).order_by(self.tasks_tbl.c.created.asc())
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
            with self.db_engine.connect() as conn:
                query = self.tasks_tbl.select().where(
                    self.tasks_tbl.c.task_id == task_id.bytes)
                rs = conn.execute(query)
                r = rs.fetchone()

            task = objects.Task.from_db(dict(r))

            self.logger.debug(
                "Assembling result messages for task %s." % str(task.task_id))
            self._assemble_tasks(task_list=[task])
            task.statemgr = self

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
            with self.db_engine.connect() as conn:
                query = self.result_message_tbl.insert().values(
                    task_id=task_id.bytes, **(msg.to_db()))
                conn.execute(query)
            return True
        except Exception as ex:
            self.logger.error("Error inserting result message for task %s: %s"
                              % (str(task_id), str(ex)))
            return False

    def delete_result_message(self, task_id, msg):
        """Delete a result message to database attached to task task_id.

        :param task_id: uuid.UUID ID of the task the msg belongs to
        :param msg: instance of objects.TaskStatusMessage
        """
        try:
            with self.db_engine.connect() as conn:
                query = self.result_message_tbl.delete().values(
                    task_id=task_id.bytes, **(msg.to_db()))
                conn.execute(query)
            return True
        except Exception as ex:
            self.logger.error("Error delete result message for task %s: %s"
                              % (str(task_id), str(ex)))
            return False

    def _assemble_tasks(self, task_list=None):
        """Attach all the appropriate result messages to the tasks in the list.

        :param task_list: a list of objects.Task instances to attach result messages to
        """
        if task_list is None:
            return None

        with self.db_engine.connect() as conn:
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

    def post_task(self, task):
        """Insert a task into the database.

        Does not insert attached result messages

        :param task: instance of objects.Task to insert into the database.
        """
        try:
            with self.db_engine.connect() as conn:
                query = self.tasks_tbl.insert().values(
                    **(task.to_db(include_id=True)))
                conn.execute(query)
            return True
        except Exception as ex:
            self.logger.error(
                "Error inserting task %s: %s" % (str(task.task_id), str(ex)))
            return False

    def put_task(self, task):
        """Update a task in the database.

        :param task: objects.Task instance to reference for update values
        """
        try:
            with self.db_engine.connect() as conn:
                query = self.tasks_tbl.update().where(
                    self.tasks_tbl.c.task_id == task.task_id.bytes).values(
                        **(task.to_db(include_id=False)))
                rs = conn.execute(query)
                if rs.rowcount == 1:
                    return True
                else:
                    return False
        except Exception as ex:
            self.logger.error(
                "Error updating task %s: %s" % (str(task.task_id), str(ex)))
            return False

    def task_retention(self, retain_days):
        """Delete all tasks in the database older than x days.

        :param days: number of days to keep tasks
        """
        with self.db_engine.connect() as conn:
            try:
                query_tasks_text = sql.text(
                    "DELETE FROM tasks WHERE created < now() - interval '"
                    + retain_days
                    + " days'").execution_options(autocommit=True)
                conn.execute(query_tasks_text)
                conn.close()
            except Exception as ex:
                self.logger.error(
                    "Error deleting tasks: %s" % str(ex))
                return False

        with self.db_engine.connect() as conn:
            try:
                query_subtasks_text = (
                    "DELETE FROM tasks "
                    "WHERE parent_task_id IS NOT NULL AND "
                    "parent_task_id NOT IN "
                    "(SELECT task_id FROM tasks);")
                conn.execute(sql.text(query_subtasks_text))
                conn.close()
            except Exception as ex:
                self.logger.error(
                    "Error deleting subtasks: %s" % str(ex))
                return False

        with self.db_engine.connect() as conn:
            try:
                query_result_message_text = (
                    "DELETE FROM result_message WHERE ts IN "
                    "(SELECT result_message.ts FROM result_message "
                    "LEFT JOIN tasks ON "
                    "result_message.task_id=tasks.task_id "
                    "WHERE tasks.task_id IS NULL);")
                conn.execute(sql.text(query_result_message_text))
                conn.close()
            except Exception as ex:
                self.logger.error(
                    "Error deleting result messages: %s" % str(ex))
                return False

        with self.db_engine.connect() as conn:
            try:
                real_conn = conn.connection
                old_isolation_level = real_conn.isolation_level
                real_conn.set_isolation_level(0)
                query_vacuum_text = sql.text("VACUUM FULL")
                conn.execute(query_vacuum_text)
                real_conn.set_isolation_level(old_isolation_level)
                conn.close()
            except Exception as ex:
                self.logger.error(
                    "Error running vacuum full: %s" % str(ex))
                return False

            return True

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
            with self.db_engine.connect() as conn:
                rs = conn.execute(
                    query_string,
                    new_subtask=subtask_id.bytes,
                    task_id=task_id.bytes)
                rc = rs.rowcount
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
            with self.db_engine.connect() as conn:
                query = self.active_instance_tbl.update().where(
                    self.active_instance_tbl.c.identity == leader_id.
                    bytes).values(last_ping=datetime.utcnow())
                rs = conn.execute(query)
                rc = rs.rowcount

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
            "identity = :instance_id, last_ping = timezone('UTC', now()) "
            "WHERE active_instance.last_ping < (now() - interval '%d seconds')"
            % (config.config_mgr.conf.leader_grace_period)).execution_options(
                autocommit=True)

        try:
            with self.db_engine.connect() as conn:
                conn.execute(query_string, instance_id=leader_id.bytes)
                check_query = self.active_instance_tbl.select().where(
                    self.active_instance_tbl.c.identity == leader_id.bytes)
                rs = conn.execute(check_query)
                r = rs.fetchone()
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
            with self.db_engine.connect() as conn:
                query = self.active_instance_tbl.delete().where(
                    self.active_instance_tbl.c.identity == leader_id.bytes)
                rs = conn.execute(query)
                rc = rs.rowcount

            if rc == 1:
                return True
            else:
                return False
        except Exception as ex:
            self.logger.error("Error abidcating leadership: %s" % str(ex))

    def post_boot_action_context(self, nodename, task_id, identity):
        """Save the context for a boot action for later access by a node.

        The ``task_id`` passed here will be maintained for the context of the boot action
        so that the design_ref can be accessed for loading the design document set. When
        status messages for the boot actions are reported, they will be attached to this task.

        :param nodename: The name of the node
        :param task_id: The uuid.UUID task id instigating the node deployment
        :param identity: A 32 byte string that the node must provide in the ``X-BootAction-Key``
                         header when accessing the boot action API
        """
        try:
            with self.db_engine.connect() as conn:
                query = sql.text(
                    "INSERT INTO boot_action AS ba1 (node_name, task_id, identity_key) "
                    "VALUES (:node, :task_id, :identity) "
                    "ON CONFLICT (node_name) DO UPDATE SET "
                    "task_id = :task_id, identity_key = :identity "
                    "WHERE ba1.node_name = :node").execution_options(
                        autocommit=True)

                conn.execute(
                    query,
                    node=nodename,
                    task_id=task_id.bytes,
                    identity=identity)

            return True
        except Exception as ex:
            self.logger.error(
                "Error posting boot action context for node %s" % nodename,
                exc_info=ex)
            return False

    def get_boot_action_context(self, nodename):
        """Get the boot action context for a node.

        Returns dictionary with ``node_name``, ``task_id`` and ``identity_key`` keys

        :param nodename: Name of the node
        """
        try:
            with self.db_engine.connect() as conn:
                query = self.boot_action_tbl.select().where(
                    self.boot_action_tbl.c.node_name == nodename)
                rs = conn.execute(query)
                r = rs.fetchone()
                if r is not None:
                    result_dict = dict(r)
                    result_dict['task_id'] = uuid.UUID(
                        bytes=bytes(result_dict['task_id']))
                    result_dict['identity_key'] = bytes(
                        result_dict['identity_key'])
                    return result_dict
                return None
        except Exception as ex:
            self.logger.error(
                "Error retrieving boot action context for node %s" % nodename,
                exc_info=ex)
            return None

    def post_boot_action(self,
                         nodename,
                         task_id,
                         identity_key,
                         action_id,
                         action_name,
                         action_status=hd_fields.ActionResult.Incomplete):
        """Post a individual boot action.

        :param nodename: The name of the node the boot action is running on
        :param task_id: The uuid.UUID task_id of the task that instigated the node deployment
        :param identity_key: A 256-bit key the node must provide when accessing the boot action API
        :param action_id: The 32-byte ULID id of the boot action
        :param action_status: The status of the action.
        """
        try:
            with self.db_engine.connect() as conn:
                query = self.ba_status_tbl.insert().values(
                    node_name=nodename,
                    action_id=action_id,
                    action_name=action_name,
                    task_id=task_id.bytes,
                    identity_key=identity_key,
                    action_status=action_status)
                conn.execute(query)
                return True
        except Exception as ex:
            self.logger.error(
                "Error saving boot action %s." % action_id, exc_info=ex)
            return False

    def put_bootaction_status(self,
                              action_id,
                              action_status=hd_fields.ActionResult.Incomplete):
        """Update the status of a bootaction.

        :param action_id: string ULID ID of the boot action
        :param action_status: The string statu to set for the boot action
        """
        try:
            with self.db_engine.connect() as conn:
                query = self.ba_status_tbl.update().where(
                    self.ba_status_tbl.c.action_id == ulid2.decode_ulid_base32(
                        action_id)).values(action_status=action_status)
                conn.execute(query)
                return True
        except Exception as ex:
            self.logger.error(
                "Error updating boot action %s status." % action_id,
                exc_info=ex)
            return False

    def get_boot_actions_for_node(self, nodename):
        """Query for getting all boot action statuses for a node.

        Return a dictionary of boot action dictionaries keyed by the
        boot action name.

        :param nodename: string nodename of the target node
        """
        try:
            with self.db_engine.connect() as conn:
                query = self.ba_status_tbl.select().where(
                    self.ba_status_tbl.c.node_name == nodename)
                rs = conn.execute(query)
                actions = dict()
                for r in rs:
                    ba_dict = dict(r)
                    ba_dict['action_id'] = bytes(ba_dict['action_id'])
                    ba_dict['identity_key'] = bytes(ba_dict['identity_key'])
                    ba_dict['task_id'] = uuid.UUID(bytes=ba_dict['task_id'])
                    actions[ba_dict.get('action_name', 'undefined')] = ba_dict
                return actions
        except Exception as ex:
            self.logger.error(
                "Error selecting boot actions for node %s" % nodename,
                exc_info=ex)
            return None

    def get_boot_action(self, action_id):
        """Query for a single boot action by ID.

        :param action_id: string ULID bootaction id
        """
        try:
            with self.db_engine.connect() as conn:
                query = self.ba_status_tbl.select().where(
                    self.ba_status_tbl.c.action_id == ulid2.decode_ulid_base32(
                        action_id))
                rs = conn.execute(query)
                r = rs.fetchone()
                if r is not None:
                    ba_dict = dict(r)
                    ba_dict['action_id'] = bytes(ba_dict['action_id'])
                    ba_dict['identity_key'] = bytes(ba_dict['identity_key'])
                    ba_dict['task_id'] = uuid.UUID(bytes=ba_dict['task_id'])
                    return ba_dict
                else:
                    return None
        except Exception as ex:
            self.logger.error(
                "Error querying boot action %s" % action_id, exc_info=ex)

    def post_build_data(self, build_data):
        """Write a new build data element to the database.

        :param build_data: objects.BuildData instance to write
        """
        try:
            with self.db_engine.connect() as conn:
                query = self.build_data_tbl.insert().values(
                    **build_data.to_db())
                conn.execute(query)
                return True
        except Exception as ex:
            self.logger.error("Error saving build data.", exc_info=ex)
            return False

    def get_build_data(self,
                       node_name=None,
                       task_id=None,
                       latest=False,
                       verbosity=2):
        """Retrieve build data from the database.

        If ``node_name`` or ``task_id`` are defined, use them as
        filters for the build_data retrieved. If ``task_id`` is not
        defined, ``latest`` determines if all build data is returned,
        or only the chronologically latest version for each generator
        description.

        :param node_name: String name of the node to filter on
        :param task_id: uuid.UUID ID of the task to filter on
        :param latest: boolean whether to return only the latest
                       version for each generator
        :param verbosity: integer of how verbose the response should
                          be. 1 is summary, 2 includes the collected data
        :returns: list of objects.BuildData instances
        """
        # TODO(sh8121att) possibly optimize queries by changing select column
        # list based on verbosity
        try:
            with self.db_engine.connect() as conn:
                if node_name and task_id:
                    query = self.build_data_tbl.select().where(
                        self.build_data_tbl.c.node_name == node_name
                        and self.build_data_tbl.c.task_id == task_id.bytes
                    ).order_by(self.build_data_tbl.c.collected_date.desc())
                    rs = conn.execute(query)
                elif node_name:
                    if latest:
                        query = sql.text(
                            'SELECT DISTINCT ON (generator) build_data.* '
                            'FROM build_data '
                            'WHERE build_data.node_name = :nodename '
                            'ORDER BY generator, build_data.collected_date DESC'
                        )
                        rs = conn.execute(query, nodename=node_name)
                    else:
                        query = self.build_data_tbl.select().where(
                            self.build_data_tbl.c.node_name == node_name)
                        rs = conn.execute(query)
                elif task_id:
                    query = self.build_data_tbl.select().where(
                        self.build_data_tbl.c.task_id == task_id.bytes)
                    rs = conn.execute(query)
                else:
                    if latest:
                        query = sql.text(
                            'SELECT DISTINCT ON (generator), build_data.* '
                            'FROM build_data '
                            'ORDER BY generator, build_data.collected.date DESC'
                        )
                        rs = conn.execute(query)
                    else:
                        query = self.build_data_tbl.select()
                        rs = conn.execute(query)

                result_data = rs.fetchall()

            return [objects.BuildData.from_db(dict(r)) for r in result_data]
        except Exception as ex:
            self.logger.error("Error selecting build data.", exc_info=ex)
            raise errors.BuildDataError("Error selecting build data.")

    def get_now(self):
        """Query the database for now() from dual.
        """
        try:
            with self.db_engine.connect() as conn:
                query = sql.text("SELECT now()")
                rs = conn.execute(query)

                r = rs.first()

                if r is not None and r.now:
                    return r.now
                else:
                    return None
        except Exception as ex:
            self.logger.error(str(ex))
            self.logger.error("Error querying for now()", exc_info=True)
            return None

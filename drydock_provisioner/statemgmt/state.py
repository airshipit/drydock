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

from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy import sql

import drydock_provisioner.objects as objects

from .db import tables

from drydock_provisioner import config

from drydock_provisioner.error import DesignError
from drydock_provisioner.error import StateError


class DrydockState(object):
    def __init__(self):
        self.logger = logging.getLogger(
            config.config_mgr.conf.logging.global_logger_name)

        self.db_engine = create_engine(
            config.config_mgr.conf.database.database_connect_string)
        self.db_metadata = MetaData()

        self.tasks_tbl = tables.Tasks(self.db_metadata)
        self.result_message_tbl = tables.ResultMessage(self.db_metadata)
        self.active_instance_tbl = tables.ActiveInstance(self.db_metadata)
        self.build_data_tbl = tables.BuildData(self.db_metadata)

        return

    # TODO(sh8121att) Need to lock a design base or change once implementation
    # has started
    def get_design(self, design_id):
        if design_id not in self.designs.keys():

            raise DesignError("Design ID %s not found" % (design_id))

        return objects.SiteDesign.obj_from_primitive(self.designs[design_id])

    def post_design(self, site_design):
        if site_design is not None:
            my_lock = self.designs_lock.acquire(blocking=True, timeout=10)
            if my_lock:
                design_id = site_design.id
                if design_id not in self.designs.keys():
                    self.designs[design_id] = site_design.obj_to_primitive()
                else:
                    self.designs_lock.release()
                    raise StateError("Design ID %s already exists" % design_id)
                self.designs_lock.release()
                return True
            raise StateError("Could not acquire lock")
        else:
            raise DesignError("Design change must be a SiteDesign instance")

    def put_design(self, site_design):
        if site_design is not None:
            my_lock = self.designs_lock.acquire(blocking=True, timeout=10)
            if my_lock:
                design_id = site_design.id
                if design_id not in self.designs.keys():
                    self.designs_lock.release()
                    raise StateError("Design ID %s does not exist" % design_id)
                else:
                    self.designs[design_id] = site_design.obj_to_primitive()
                    self.designs_lock.release()
                    return True
            raise StateError("Could not acquire lock")
        else:
            raise DesignError("Design base must be a SiteDesign instance")

    def get_current_build(self):
        latest_stamp = 0
        current_build = None

        for b in self.builds:
            if b.build_id > latest_stamp:
                latest_stamp = b.build_id
                current_build = b

        return deepcopy(current_build)

    def get_build(self, build_id):
        for b in self.builds:
            if b.build_id == build_id:
                return b

        return None

    def post_build(self, site_build):
        if site_build is not None and isinstance(site_build, SiteBuild):
            my_lock = self.builds_lock.acquire(block=True, timeout=10)
            if my_lock:
                exists = [
                    b for b in self.builds if b.build_id == site_build.build_id
                ]

                if len(exists) > 0:
                    self.builds_lock.release()
                    raise DesignError("Already a site build with ID %s" %
                                      (str(site_build.build_id)))
                self.builds.append(deepcopy(site_build))
                self.builds_lock.release()
                return True
            raise StateError("Could not acquire lock")
        else:
            raise DesignError("Design change must be a SiteDesign instance")

    def put_build(self, site_build):
        if site_build is not None and isinstance(site_build, SiteBuild):
            my_lock = self.builds_lock.acquire(block=True, timeout=10)
            if my_lock:
                buildid = site_build.buildid
                for b in self.builds:
                    if b.buildid == buildid:
                        b.merge_updates(site_build)
                        self.builds_lock.release()
                        return True
                self.builds_lock.release()
                return False
            raise StateError("Could not acquire lock")
        else:
            raise DesignError("Design change must be a SiteDesign instance")

    def get_tasks(self):
        """Get all tasks in the database."""
        try:
            conn = self.db_engine.connect()
            query = sql.select([self.tasks_tbl])
            rs = conn.execute(query)

            task_list = [objects.Task.from_db(dict(r)) for r in rs]

            self._assemble_tasks(task_list=task_list)

            conn.close()

            return task_list
        except Exception as ex:
            self.logger.error("Error querying task list: %s" % str(ex))
            return []

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

            self.logger.debug("Assembling result messages for task %s." % str(task.task_id))
            self._assemble_tasks(task_list=[task])

            conn.close()

            return task

        except Exception as ex:
            self.logger.error("Error querying task %s: %s" % (str(task_id),
                                                              str(ex)), exc_info=True)
            return None

    def post_result_message(self, task_id, msg):
        """Add a result message to database attached to task task_id.

        :param task_id: uuid.UUID ID of the task the msg belongs to
        :param msg: instance of objects.TaskStatusMessage
        """
        try:
            conn = self.db_engine.connect()
            query = self.result_message_tbl.insert().values(task_id=task_id.bytes, **(msg.to_db()))
            conn.execute(query)
            conn.close()
            return True
        except Exception as ex:
            self.logger.error("Error inserting result message for task %s: %s" % (str(task_id), str(ex)))
            return False

    def _assemble_tasks(self, task_list=None):
        """Attach all the appropriate result messages to the tasks in the list.

        :param task_list: a list of objects.Task instances to attach result messages to
        """
        if task_list is None:
            return None

        conn = self.db_engine.connect()
        query = sql.select([self.result_message_tbl]).where(
            self.result_message_tbl.c.task_id == sql.bindparam(
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
            query = self.tasks_tbl.insert().values(**(task.to_db(include_id=True)))
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
            query = self.tasks_tbl.update(
                **(task.to_db(include_id=False))).where(
                    self.tasks_tbl.c.task_id == task.task_id.bytes)
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
        query_string = sql.text("UPDATE tasks "
                                "SET subtask_id_list = array_append(subtask_id_list, :new_subtask) "
                                "WHERE task_id = :task_id").execution_options(autocommit=True)

        try:
            conn = self.db_engine.connect()
            rs = conn.execute(query_string, new_subtask=subtask_id.bytes, task_id=task_id.bytes)
            rc = rs.rowcount
            conn.close()
            if rc == 1:
                return True
            else:
                return False
        except Exception as ex:
            self.logger.error("Error appending subtask %s to task %s: %s"
                              % (str(subtask_id), str(task_id), str(ex)))
            return False

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
        query_string = sql.text("INSERT INTO active_instance (dummy_key, identity, last_ping) "
                                "VALUES (1, :instance_id, timezone('UTC', now())) "
                                "ON CONFLICT (dummy_key) DO UPDATE SET "
                                "identity = :instance_id "
                                "WHERE active_instance.last_ping < (now() - interval '%d seconds')"
                                % (config.config_mgr.conf.default.leader_grace_period)).execution_options(autocommit=True)

        try:
            conn = self.db_engine.connect()
            rs = conn.execute(query_string, instance_id=leader_id.bytes)
            rc = rs.rowcount
            conn.close()
            if rc == 1:
                return True
            else:
                return False
        except Exception as ex:
            self.logger.error("Error executing leadership claim: %s" % str(ex))
            return False

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

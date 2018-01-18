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
"""Definitions for Drydock database tables."""

from sqlalchemy.schema import Table, Column
from sqlalchemy.types import Boolean, DateTime, String, Integer, Text
from sqlalchemy.dialects import postgresql as pg


class ExtendTable(Table):
    def __new__(cls, metadata):
        self = super().__new__(cls, cls.__tablename__, metadata,
                               *cls.__schema__)
        return self


class Tasks(ExtendTable):
    """Table for persisting Tasks."""

    __tablename__ = 'tasks'

    __schema__ = [
        Column('task_id', pg.BYTEA(16), primary_key=True),
        Column('parent_task_id', pg.BYTEA(16)),
        Column('subtask_id_list', pg.ARRAY(pg.BYTEA(16))),
        Column('result_status', String(32)),
        Column('result_message', String(128)),
        Column('result_reason', String(128)),
        Column('result_error_count', Integer),
        Column('result_successes', pg.ARRAY(String(32))),
        Column('result_failures', pg.ARRAY(String(32))),
        Column('retry', Integer),
        Column('status', String(32)),
        Column('created', DateTime),
        Column('created_by', String(16)),
        Column('updated', DateTime),
        Column('design_ref', String(128)),
        Column('request_context', pg.JSON),
        Column('node_filter', pg.JSON),
        Column('action', String(32)),
        Column('terminated', DateTime),
        Column('terminated_by', String(16)),
        Column('terminate', Boolean, default=False)
    ]


class ResultMessage(ExtendTable):
    """Table for tracking result/status messages."""

    __tablename__ = 'result_message'

    __schema__ = [
        Column('sequence', Integer, primary_key=True),
        Column('task_id', pg.BYTEA(16)),
        Column('message', String(1024)),
        Column('error', Boolean),
        Column('context', String(64)),
        Column('context_type', String(16)),
        Column('ts', DateTime),
        Column('extra', pg.JSON)
    ]


class ActiveInstance(ExtendTable):
    """Table to organize multiple orchestrator instances."""

    __tablename__ = 'active_instance'

    __schema__ = [
        Column('dummy_key', Integer, primary_key=True),
        Column('identity', pg.BYTEA(16)),
        Column('last_ping', DateTime),
    ]


class BootAction(ExtendTable):
    """Table persisting node build data."""

    __tablename__ = 'boot_action'

    __schema__ = [
        Column('node_name', String(280), primary_key=True),
        Column('task_id', pg.BYTEA(16)),
        Column('identity_key', pg.BYTEA(32)),
    ]


class BootActionStatus(ExtendTable):
    """Table tracking status of node boot actions."""

    __tablename__ = 'boot_action_status'

    __schema__ = [
        Column('node_name', String(280), index=True),
        Column('action_id', pg.BYTEA(16), primary_key=True),
        Column('action_name', String(64)),
        Column('task_id', pg.BYTEA(16), index=True),
        Column('identity_key', pg.BYTEA(32)),
        Column('action_status', String(32)),
    ]


class BuildData(ExtendTable):
    """Table for persisting node build data."""

    __tablename__ = 'build_data'

    __schema__ = [
        Column('node_name', String(32), index=True),
        Column('task_id', pg.BYTEA(16), index=True),
        Column('collected_date', DateTime),
        Column('generator', String(256)),
        Column('data_format', String(32)),
        Column('data_element', Text),
    ]

"""Definitions for Drydock database tables."""

from sqlalchemy import Table, Column, MetaData
from sqlalchemy.types import Boolean, DateTime, String, Integer, JSON, BLOB
from sqlalchemy.dialects import postgresql as pg

metadata = MetaData()

class Tasks(Table):
    """Table for persisting Tasks."""

    __tablename__ = 'tasks'

    __schema__ = [
        Column('task_id', pg.BYTEA(16), primary_key=True),
        Column('parent_task_id', pg.BYTEA(16)),
        Column('subtask_id_list', pg.ARRAY(pg.BYTEA(16))),
        Column('result_status', String(32)),
        Column('result_error_count', Integer),
        Column('status', String(32)),
        Column('created', DateTime),
        Column('created_by', String(16)),
        Column('updated', DateTime),
        Column('design_ref', String(128)),
        Column('request_context', pg.JSON),
        Column('action', String(32)),
        Column('terminated', DateTime),
        Column('terminated_by', String(16))
    ]

    def __init__(self):
        super().__init__(
            Tasks.__tablename__,
            metadata,
            *Tasks.__schema__)


class ResultMessage(Table):
    """Table for tracking result/status messages."""

    __tablename__ = 'result_message'

    __schema__ = [
        Column('task_id', pg.BYTEA(16), primary_key=True),
        Column('sequence', Integer, autoincrement='auto', primary_key=True),
        Column('message', String(128)),
        Column('error', Boolean),
        Column('extra', pg.JSON)
    ]

    def __init__(self):
        super().__init__(
            ResultMessage.__tablename__,
            metadata,
            *ResultMessage.__schema__)


class ActiveInstance(Table):
    """Table to organize multiple orchestrator instances."""

    __tablename__ = 'active_instance'

    __schema__ = [
        Column('identity', pg.BYTEA(16), primary_key=True),
        Column('last_ping', DateTime)
    ]

    def __init__(self):
        super().__init__(
            ActiveInstance.__tablename__,
            metadata,
            *ActiveInstance.__schema__)


class BuildData(Table):
    """Table persisting node build data."""

    __tablename__ = 'build_data'

    __schema__ = [
        Column('node_name', String(16), primary_key=True),
        Column('task_id', pg.BYTEA(16)),
        Column('message', String(128)),
    ]

    def __init__(self):
        super().__init__(
            BuildData.__tablename__,
            metadata,
            *BuildData.__schema__)

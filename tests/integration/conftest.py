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
"""Shared fixtures used by integration tests."""
import logging

from oslo_config import cfg

import drydock_provisioner.config as config
import drydock_provisioner.objects as objects

from drydock_provisioner.statemgmt.state import DrydockState

import pytest


@pytest.fixture()
def blank_state(drydock_state):
    drydock_state.tabularasa()
    return drydock_state


@pytest.fixture(scope='session')
def drydock_state(setup):
    state_mgr = DrydockState()
    state_mgr.connect_db()
    return state_mgr


@pytest.fixture(scope='session')
def setup():
    objects.register_all()
    logging.basicConfig(level='DEBUG')

    req_opts = {
        'default':
        [cfg.IntOpt('leader_grace_period'),
         cfg.IntOpt('poll_interval')],
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
        override="postgresql+psycopg2://drydock:drydock@localhost:5432/drydock"
    )
    config.config_mgr.conf.set_override(
        name="leader_grace_period", group="default", override=15)
    config.config_mgr.conf.set_override(
        name="poll_interval", group="default", override=3)
    return

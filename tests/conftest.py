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
import os
import shutil
from unittest.mock import Mock

import drydock_provisioner.config as config
import drydock_provisioner.objects as objects

from drydock_provisioner.statemgmt.state import DrydockState
from drydock_provisioner.ingester.ingester import Ingester
from drydock_provisioner.orchestrator.orchestrator import Orchestrator

import pytest


@pytest.fixture()
def deckhand_ingester():
    ingester = Ingester()
    ingester.enable_plugin(
        'drydock_provisioner.ingester.plugins.deckhand.DeckhandIngester')
    return ingester


@pytest.fixture()
def yaml_ingester():
    ingester = Ingester()
    ingester.enable_plugin(
        'drydock_provisioner.ingester.plugins.yaml.YamlIngester')
    return ingester


@pytest.fixture()
def deckhand_orchestrator(drydock_state, deckhand_ingester):
    orchestrator = Orchestrator(
        state_manager=drydock_state, ingester=deckhand_ingester)
    return orchestrator


@pytest.fixture()
def yaml_orchestrator(drydock_state, yaml_ingester):
    orchestrator = Orchestrator(
        state_manager=drydock_state, ingester=yaml_ingester)
    return orchestrator


@pytest.fixture()
def blank_state(drydock_state):
    drydock_state.tabularasa()
    return drydock_state


@pytest.fixture(scope='session')
def drydock_state(setup):
    state_mgr = DrydockState()
    state_mgr.connect_db()
    return state_mgr


@pytest.fixture(scope='module')
def input_files(tmpdir_factory, request):
    tmpdir = tmpdir_factory.mktemp('data')
    samples_dir = os.path.dirname(os.getenv('YAMLDIR'))
    samples = os.listdir(samples_dir)

    for f in samples:
        src_file = samples_dir + "/" + f
        dst_file = str(tmpdir) + "/" + f
        shutil.copyfile(src_file, dst_file)

    return tmpdir


@pytest.fixture(scope='session')
def setup(setup_logging):
    objects.register_all()

    config.config_mgr.register_options(enable_keystone=False)

    config.config_mgr.conf([])
    config.config_mgr.conf.set_override(
        name="node_driver",
        group="plugins",
        override=
        "drydock_provisioner.drivers.node.maasdriver.driver.MaasNodeDriver")
    config.config_mgr.conf.set_override(
        name="database_connect_string",
        group="database",
        override="postgresql+psycopg2://drydock:drydock@localhost:5432/drydock"
    )
    config.config_mgr.conf.set_override(
        name="leader_grace_period", override=15)
    config.config_mgr.conf.set_override(name="poll_interval", override=3)
    return


@pytest.fixture(scope='session')
def setup_logging():
    # Setup root logger
    logger = logging.getLogger('drydock')
    logger.setLevel('DEBUG')
    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s'
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Specalized format for API logging
    logger = logging.getLogger('drydock.control')
    logger.propagate = False
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(user)s - %(req_id)s - %(external_ctx)s - %(message)s'
    )

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)


@pytest.fixture(scope='module')
def mock_get_build_data(drydock_state):
    def side_effect(**kwargs):
        build_data = objects.BuildData(
            node_name="test",
            task_id="tid",
            generator="lshw",
            data_format="text/plain",
            data_element="<mocktest></mocktest>")
        return [build_data]

    drydock_state.real_get_build_data = drydock_state.get_build_data
    drydock_state.get_build_data = Mock(side_effect=side_effect)

    yield
    drydock_state.get_build_data = Mock(wraps=None, side_effect=None)
    drydock_state.get_build_data = drydock_state.real_get_build_data

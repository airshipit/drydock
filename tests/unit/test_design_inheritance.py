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

import pytest
import shutil
import os
import logging

from oslo_config import cfg

import drydock_provisioner.config as config
import drydock_provisioner.objects as objects

from drydock_provisioner.ingester.ingester import Ingester
from drydock_provisioner.statemgmt.state import DrydockState
from drydock_provisioner.orchestrator.orchestrator import Orchestrator

logging.basicConfig(level=logging.DEBUG)


class TestClass(object):
    def test_design_inheritance(self, input_files, setup):
        input_file = input_files.join("fullsite.yaml")

        design_state = DrydockState()
        design_ref = "file://%s" % str(input_file)

        ingester = Ingester()
        ingester.enable_plugin(
            'drydock_provisioner.ingester.plugins.yaml.YamlIngester')

        orchestrator = Orchestrator(
            state_manager=design_state, ingester=ingester)

        design_status, design_data = orchestrator.get_effective_site(
            design_ref)

        assert len(design_data.baremetal_nodes) == 2

        node = design_data.get_baremetal_node("controller01")

        assert node.hardware_profile == 'HPGen9v3'

        iface = node.get_applied_interface('bond0')

        assert len(iface.get_hw_slaves()) == 2

        iface = node.get_applied_interface('pxe')

        assert len(iface.get_hw_slaves()) == 1

    @pytest.fixture(scope='module')
    def input_files(self, tmpdir_factory, request):
        tmpdir = tmpdir_factory.mktemp('data')
        samples_dir = os.path.dirname(str(
            request.fspath)) + "/" + "../yaml_samples"
        samples = os.listdir(samples_dir)

        for f in samples:
            src_file = samples_dir + "/" + f
            dst_file = str(tmpdir) + "/" + f
            shutil.copyfile(src_file, dst_file)

        return tmpdir

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

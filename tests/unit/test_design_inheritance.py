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

from drydock_provisioner.ingester import Ingester
from drydock_provisioner.statemgmt import DesignState
from drydock_provisioner.orchestrator import Orchestrator

from copy import deepcopy

import pytest
import shutil
import os
import drydock_provisioner.ingester.plugins.yaml
import yaml

class TestClass(object):


    def test_design_inheritance(self, loaded_design):
        orchestrator = Orchestrator(state_manager=loaded_design,
                                    enabled_drivers={'oob': 'drydock_provisioner.drivers.oob.pyghmi_driver.PyghmiDriver'})

        design_data = orchestrator.load_design_data("sitename")

        assert len(design_data.baremetal_nodes) == 2

        design_data = orchestrator.compute_model_inheritance(design_data)

        node = design_data.get_baremetal_node("controller01")

        assert node.applied.get('hardware_profile') == 'HPGen9v3'

        iface = node.get_applied_interface('bond0')

        assert iface.get_applied_slave_count() == 2

        iface = node.get_applied_interface('pxe')

        assert iface.get_applied_slave_count() == 1

    @pytest.fixture(scope='module')
    def loaded_design(self, input_files):
        input_file = input_files.join("fullsite.yaml")

        design_state = DesignState()
        design_data = SiteDesign()
        design_state.post_design_base(design_data)

        ingester = Ingester()
        ingester.enable_plugins([drydock_provisioner.ingester.plugins.yaml.YamlIngester])
        ingester.ingest_data(plugin_name='yaml', design_state=design_state, filenames=[str(input_file)])

        return design_state

    @pytest.fixture(scope='module')
    def input_files(self, tmpdir_factory, request):
        tmpdir = tmpdir_factory.mktemp('data')
        samples_dir = os.path.dirname(str(request.fspath)) + "../yaml_samples"
        samples = os.listdir(samples_dir)

        for f in samples:
            src_file = samples_dir + "/" + f
            dst_file = str(tmpdir) + "/" + f
            shutil.copyfile(src_file, dst_file)

        return tmpdir

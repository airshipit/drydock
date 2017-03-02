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

from helm_drydock.ingester import Ingester
from helm_drydock.statemgmt import DesignState
from helm_drydock.orchestrator.designdata import DesignStateClient

from copy import deepcopy

import pytest
import shutil
import os
import helm_drydock.ingester.plugins.yaml
import yaml

class TestClass(object):

    def setup_method(self, method):
        print("Running test {0}".format(method.__name__))


    def test_design_inheritance(self, loaded_design):
        client = DesignStateClient()

        design_data = client.load_design_data("sitename", design_state=loaded_design)
        design_data = client.compute_model_inheritance(design_data)

        node = design_data.get_baremetal_node("controller01")

        print(yaml.dump(node, default_flow_style=False))
        
        assert node.hardware_profile == 'HPGen9v3'

        iface = node.get_interface('bond0')

        assert iface.get_slave_count() == 2

        iface = node.get_interface('pxe')

        assert iface.get_slave_count() == 1

    @pytest.fixture(scope='module')
    def loaded_design(self, input_files):
        input_file = input_files.join("fullsite.yaml")

        module_design_state = DesignState()

        ingester = Ingester()
        ingester.enable_plugins([helm_drydock.ingester.plugins.yaml.YamlIngester])
        ingester.ingest_data(plugin_name='yaml', design_state=module_design_state, filenames=[str(input_file)])

        return module_design_state

        

    @pytest.fixture(scope='module')
    def input_files(self, tmpdir_factory, request):
        tmpdir = tmpdir_factory.mktemp('data')
        samples_dir = os.path.dirname(str(request.fspath)) + "/yaml_samples"
        samples = os.listdir(samples_dir)

        for f in samples:
            src_file = samples_dir + "/" + f
            dst_file = str(tmpdir) + "/" + f
            shutil.copyfile(src_file, dst_file)

        return tmpdir
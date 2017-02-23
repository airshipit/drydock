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

import pytest
import shutil
import os
import helm_drydock.ingester.plugins.aicyaml

class TestClass(object):

    def setup_method(self, method):
        print("Running test {0}".format(method.__name__))

    def test_ingest_full_site(self, design_state,input_files):
        input_file = input_files.join("fullsite.yaml")

        ingester = Ingester()
        ingester.enable_plugins([helm_drydock.ingester.plugins.aicyaml.AicYamlIngester])
        ingester.ingest_data(plugin_name='aic_yaml', design_state=design_state, filenames=[str(input_file)])

        assert len(design_state.host_profiles) == 3

    @pytest.fixture(scope='module')
    def input_files(self, tmpdir_factory, request):
        tmpdir = tmpdir_factory.mktemp('data')
        samples_dir = os.path.dirname(str(request.fspath)) + "/aicyaml_samples"
        samples = os.listdir(samples_dir)

        for f in samples:
            src_file = samples_dir + "/" + f
            dst_file = str(tmpdir) + "/" + f
            shutil.copyfile(src_file, dst_file)

        return tmpdir

    @pytest.fixture(scope='session')
    def design_state(self):
        design_state = DesignState()
        return design_state
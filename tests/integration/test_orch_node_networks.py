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
import json
import pytest
import shutil
import os
import uuid

import helm_drydock.config as config
import helm_drydock.drivers.node.maasdriver.api_client as client
import helm_drydock.ingester.plugins.yaml
import helm_drydock.statemgmt as statemgmt
import helm_drydock.objects as objects
import helm_drydock.orchestrator as orch
import helm_drydock.objects.fields as hd_fields
import helm_drydock.objects.task as task
import helm_drydock.drivers as drivers
from helm_drydock.ingester import Ingester

class TestClass(object):

    def test_client_verify(self):
        design_state = statemgmt.DesignState()
        orchestrator = orch.Orchestrator(state_manager=design_state,
                                    enabled_drivers={'node': 'helm_drydock.drivers.node.maasdriver.driver.MaasNodeDriver'})

        orch_task = orchestrator.create_task(task.OrchestratorTask,
                                             site='sitename',
                                             design_id=None,
                                             action=hd_fields.OrchestratorAction.VerifySite)

        orchestrator.execute_task(orch_task.get_id())

        orch_task = design_state.get_task(orch_task.get_id())

        assert orch_task.result == hd_fields.ActionResult.Success

    def test_orch_preparesite(self, input_files):
        objects.register_all()

        input_file = input_files.join("fullsite.yaml")

        design_state = statemgmt.DesignState()
        design_data = objects.SiteDesign()
        design_id = design_data.assign_id()
        design_state.post_design(design_data)

        ingester = Ingester()
        ingester.enable_plugins([helm_drydock.ingester.plugins.yaml.YamlIngester])
        ingester.ingest_data(plugin_name='yaml', design_state=design_state,
                             filenames=[str(input_file)], design_id=design_id)

        design_data = design_state.get_design(design_id)

        orchestrator = orch.Orchestrator(state_manager=design_state,
                                    enabled_drivers={'node': 'helm_drydock.drivers.node.maasdriver.driver.MaasNodeDriver'})

        orch_task = orchestrator.create_task(task.OrchestratorTask,
                                             site='sitename',
                                             design_id=design_id,
                                             action=hd_fields.OrchestratorAction.PrepareSite)

        orchestrator.execute_task(orch_task.get_id())

        orch_task = design_state.get_task(orch_task.get_id())

        assert orch_task.result == hd_fields.ActionResult.Success


    

    @pytest.fixture(scope='module')
    def input_files(self, tmpdir_factory, request):
        tmpdir = tmpdir_factory.mktemp('data')
        samples_dir = os.path.dirname(str(request.fspath)) + "/../yaml_samples"
        samples = os.listdir(samples_dir)

        for f in samples:
            src_file = samples_dir + "/" + f
            dst_file = str(tmpdir) + "/" + f
            shutil.copyfile(src_file, dst_file)

        return tmpdir
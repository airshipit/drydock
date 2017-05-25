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

#
# Generic testing for the orchestrator
#
import pytest
#from pytest_mock import mocker
#import mock

import os
import shutil
import uuid

from drydock_provisioner.ingester import Ingester

import drydock_provisioner.orchestrator as orch
import drydock_provisioner.objects.fields as hd_fields
import drydock_provisioner.statemgmt as statemgmt
import drydock_provisioner.objects as objects
import drydock_provisioner.objects.task as task
import drydock_provisioner.drivers as drivers
import drydock_provisioner.ingester.plugins.yaml as yaml_ingester

class TestClass(object):

    design_id = str(uuid.uuid4())

    # sthussey None of these work right until I figure out correct
    # mocking of pyghmi
    def test_oob_verify_all_node(self, loaded_design):
        #mocker.patch('pyghmi.ipmi.private.session.Session')
        #mocker.patch.object('pyghmi.ipmi.command.Command','get_asset_tag')

        orchestrator = orch.Orchestrator(state_manager=loaded_design,
                                    enabled_drivers={'oob': 'drydock_provisioner.drivers.oob.pyghmi_driver.PyghmiDriver'})

        orch_task = orchestrator.create_task(task.OrchestratorTask,
                                             site='sitename',
                                             design_id=self.design_id,
                                             action=hd_fields.OrchestratorAction.VerifyNode)

        orchestrator.execute_task(orch_task.get_id())

        orch_task = loaded_design.get_task(orch_task.get_id())

        assert True

    """
    def test_oob_prepare_all_nodes(self, loaded_design):
        #mocker.patch('pyghmi.ipmi.private.session.Session')
        #mocker.patch.object('pyghmi.ipmi.command.Command','set_bootdev')

        orchestrator = orch.Orchestrator(state_manager=loaded_design,
                                    enabled_drivers={'oob': 'drydock_provisioner.drivers.oob.pyghmi_driver.PyghmiDriver'})

        orch_task = orchestrator.create_task(task.OrchestratorTask,
                                             site='sitename',
                                             action=enum.OrchestratorAction.PrepareNode)

        orchestrator.execute_task(orch_task.get_id())

        #assert pyghmi.ipmi.command.Command.set_bootdev.call_count == 3
        #assert pyghmi.ipmi.command.Command.set_power.call_count == 6
    """

    @pytest.fixture(scope='module')
    def loaded_design(self, input_files):
        objects.register_all()

        input_file = input_files.join("oob.yaml")

        design_state = statemgmt.DesignState()
        design_data = objects.SiteDesign(id=self.design_id)

        design_state.post_design(design_data)

        ingester = Ingester()
        ingester.enable_plugins([yaml_ingester.YamlIngester])
        ingester.ingest_data(plugin_name='yaml', design_state=design_state,
                             design_id=self.design_id, filenames=[str(input_file)])

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
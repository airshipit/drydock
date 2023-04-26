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
import pylibyaml  # noqa: F401  # patch pyyaml to use libyaml bindings
import yaml
import pytest

from click.testing import CliRunner

import drydock_provisioner.drydock_client.session as dc_session
import drydock_provisioner.drydock_client.client as dc_client

from drydock_provisioner.cli.task.actions import TaskCreate
from drydock_provisioner.cli.task.actions import TaskBuildData

import drydock_provisioner.cli.commands as cli


def test_taskcli_blank_nodefilter():
    """If no filter values are specified, node filter should be None."""

    host = 'foo.bar.baz'

    dd_ses = dc_session.DrydockSession(host)
    dd_client = dc_client.DrydockClient(dd_ses)

    action = TaskCreate(dd_client,
                        "http://foo.bar",
                        action_name="deploy_nodes")

    assert action.node_filter is None


def test_taskcli_builddata_action(mocker):
    """Test the CLI task get build data routine."""
    task_id = "aaaa-bbbb-cccc-dddd"
    build_data = [{
        "node_name": "foo",
        "task_id": task_id,
        "collected_data": "1/1/2000",
        "generator": "test",
        "data_format": "text/plain",
        "data_element": "Hello World!",
    }]

    api_client = mocker.MagicMock()
    api_client.get_task_build_data.return_value = build_data

    bd_action = TaskBuildData(api_client, task_id)

    assert bd_action.invoke() == build_data
    api_client.get_task_build_data.assert_called_with(task_id)


@pytest.mark.skip(reason='Working on mocking needed for click.testing')
def test_taskcli_builddata_command(mocker):
    """Test the CLI task get build data command."""
    task_id = "aaaa-bbbb-cccc-dddd"
    build_data = [{
        "node_name": "foo",
        "task_id": task_id,
        "collected_data": "1/1/2000",
        "generator": "test",
        "data_format": "text/plain",
        "data_element": "Hello World!",
    }]

    api_client = mocker.MagicMock()
    api_client.get_task_build_data.return_value = build_data

    mocker.patch('drydock_provisioner.cli.commands.DrydockClient',
                 new=api_client)
    mocker.patch('drydock_provisioner.cli.commands.KeystoneClient')

    runner = CliRunner()
    result = runner.invoke(
        cli.drydock, ['-u', 'http://foo', 'task', 'builddata', '-t', task_id])

    print(result.exc_info)
    api_client.get_task_build_data.assert_called_with(task_id)

    assert yaml.safe_dump(build_data,
                          allow_unicode=True,
                          default_flow_style=False) in result.output

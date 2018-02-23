
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
import drydock_provisioner.drydock_client.session as dc_session
import drydock_provisioner.drydock_client.client as dc_client

from drydock_provisioner.cli.task.actions import TaskCreate

def test_taskcli_blank_nodefilter():
    """If no filter values are specified, node filter should be None."""

    host = 'foo.bar.baz'

    dd_ses = dc_session.DrydockSession(host)
    dd_client = dc_client.DrydockClient(dd_ses)

    action = TaskCreate(dd_client,
                        "http://foo.bar",
                        action_name="deploy_nodes")

    assert action.node_filter is None

# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
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
"""Testing the ConfigureNodeProvisioner action."""
from drydock_provisioner import objects
from drydock_provisioner.drivers.node.maasdriver.actions.node import ConfigureNodeProvisioner


class TestActionConfigureNodeProvisioner(object):
    def test_create_maas_repo(selfi, mocker):
        distribution_list = ['xenial', 'xenial-updates']

        repo_obj = objects.Repository(name='foo',
                                      url='https://foo.com/repo',
                                      repo_type='apt',
                                      gpgkey="-----START STUFF----\nSTUFF\n-----END STUFF----\n",
                                      distributions=distribution_list,
                                      components=['main'])

        maas_model = ConfigureNodeProvisioner.create_maas_repo(mocker.MagicMock(), repo_obj)

        assert maas_model.distributions == ",".join(distribution_list)

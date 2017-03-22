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
from helm_drydock.statemgmt import SiteDesign

import helm_drydock.model.site as site
import helm_drydock.model.network as network

import pytest
import shutil
import os
import helm_drydock.ingester.plugins.yaml

class TestClass(object):

    def setup_method(self, method):
        print("Running test {0}".format(method.__name__))

    def test_sitedesign_merge(self):
        design_data = SiteDesign()

        initial_site = site.Site(**{'apiVersion': 'v1.0',
                                    'metadata': {
                                        'name': 'testsite',
                                    },
                                })
        net_a = network.Network(**{ 'apiVersion': 'v1.0',
                                    'metadata': {
                                        'name': 'net_a',
                                        'region': 'testsite',
                                    },
                                    'spec': {
                                        'cidr': '172.16.0.0/24',
                                }})
        net_b = network.Network(**{ 'apiVersion': 'v1.0',
                                    'metadata': {
                                        'name': 'net_b',
                                        'region': 'testsite',
                                    },
                                    'spec': {
                                        'cidr': '172.16.0.1/24',
                                }})

        design_data.add_site(initial_site)
        design_data.add_network(net_a)

        design_update = SiteDesign()
        design_update.add_network(net_b)

        design_data.merge_updates(design_update)

        assert len(design_data.get_networks()) == 2
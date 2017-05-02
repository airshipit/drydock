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


import helm_drydock.objects as objects
import helm_drydock.statemgmt as statemgmt

class TestClass(object):

    def setup_method(self, method):
        print("Running test {0}".format(method.__name__))

    def test_sitedesign_post(self):
        objects.register_all()

        state_manager = statemgmt.DesignState()
        design_data = objects.SiteDesign()
        design_id = design_data.assign_id()

        initial_site = objects.Site()
        initial_site.name = 'testsite'

        net_a = objects.Network()
        net_a.name = 'net_a'
        net_a.region = 'testsite'
        net_a.cidr = '172.16.0.0/24'

        design_data.set_site(initial_site)
        design_data.add_network(net_a)

        state_manager.post_design(design_data)

        my_design = state_manager.get_design(design_id)

        assert design_data.obj_to_primitive() == my_design.obj_to_primitive()
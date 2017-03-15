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

# OOB:
# sync_hardware_clock
# collect_chassis_sysinfo
# enable_netboot
# initiate_reboot
# set_power_off
# set_power_on

from helm_drydock.drivers import ProviderDriver

class OobDriver(ProviderDriver):

    def __init__(self):
        pass

    def execute_action(self, action, **kwargs):
        if action == 



class OobAction(Enum):
    ConfigNodePxe = 'config_node_pxe'
    SetNodeBoot = 'set_node_boot'
    PowerOffNode = 'power_off_node'
    PowerOnNode = 'power_on_node'
    PowerCycleNode = 'power_cycle_node'
    InterrogateNode = 'interrogate_node'


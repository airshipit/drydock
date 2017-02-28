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

#
# Read application configuration
#

# configuration map with defaults

class DrydockConfig(object):

	def __init__(self):
        self.server_driver_config = {
            selected_driver = helm_drydock.drivers.server.maasdriver,
            params = {
                maas_api_key = "" 
                maas_api_url = ""
            }
        }
		self.selected_network_driver = helm_drydock.drivers.network.noopdriver
		self.control_config = {}
		self.ingester_config = {
			plugins = [helm_drydock.ingester.plugins.aicyaml.AicYamlIngester]
		}
		self.introspection_config = {}
		self.orchestrator_config = {}
		self.statemgmt_config = {
			backend_driver = helm_drydock.drivers.statemgmt.etcd,
		}

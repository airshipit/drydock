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

    global_config = {
        'log_level':    'DEBUG',
    }

    node_driver = {
        'maasdriver':   {
            'api_key':  'UTBfxGL69XWjaffQek:NuKZSYGuBs6ZpYC6B9:byvXBgY8CsW5VQKxGdQjvJXtjXwr5G4U',
            'api_url':  'http://10.23.19.16:30773/MAAS/api/2.0/',
        },
    }

    ingester_config = {
        'plugins': ['drydock_provisioner.ingester.plugins.yaml.YamlIngester'],
    }

    orchestrator_config = {
        'drivers': {
            'oob': 'drydock_provisioner.drivers.oob.pyghmi_driver.PyghmiDriver',
            'node': 'drydock_provisioner.drivers.node.maasdriver.driver.MaasNodeDriver',
        }
    }
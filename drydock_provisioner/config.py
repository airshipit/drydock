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
from oslo_config import cfg

class DrydockConfig(object):
    """
    Initialize all the core options
    """
    # Core/General options
    logging_options = [
        cfg.StrOpt('log_level', default='INFO', help='Global log level for Drydock'),
        cfg.StrOpt('global_logger_name', default='drydock', help='Logger name for the top-level logger'),
        cfg.StrOpt('oobdriver_logger_name', default='${global_logger_name}.oobdriver'),
        cfg.StrOpt('nodedriver_logger_name', default='${global_logger_name}.nodedriver'),
        cfg.StrOpt('control_logger_name', default='${global_logger_name}.control'),
    ]

    # API Authentication options
    auth_options = [
        cfg.StrOpt('admin_token', default='bigboss', help='X-Auth-Token value to bypass backend authentication'),
        cfg.BoolOpt('bypass_enabled', default=False, help='Can backend authentication be bypassed?'),
    ]

    # Enabled plugins
    plugin_options = [
        cfg.MultiStrOpt('ingester',
                        default=['drydock_provisioner.ingester.plugins.yaml.YamlIngester'],
                        help='Module path string of a input ingester to enable'),
        cfg.MultiStrOpt('oob_driver',
                        default=['drydock_provisioner.drivers.oob.pyghmi_driver.PyghmiDriver'],
                        help='Module path string of a OOB driver to enable'),
        cfg.StrOpt('node_driver',
                    default='drydock_provisioner.drivers.node.maasdriver.driver.MaasNodeDriver',
                    help='Module path string of the Node driver to enable'),
        cfg.StrOpt('network_driver',
                    default=None, help='Module path string of the Network driver to enable'),
    ]

    # Timeouts for various tasks specified in minutes
    timeout_options = [
        cfg.IntOpt('create_network_template',default=2,help='Timeout in minutes for creating site network templates'),
        cfg.IntOpt('identify_node',default=10,help='Timeout in minutes for initial node identification'),
        cfg.IntOpt('configure_hardware',default=30,help='Timeout in minutes for node commissioning and hardware configuration'),
        cfg.IntOpt('apply_node_networking',default=5,help='Timeout in minutes for configuring node networking'),
        cfg.IntOpt('deploy_node',default=45,help='Timeout in minutes for deploying a node'),
    ]

    def __init__(self):
        self.conf = cfg.ConfigOpts()

        self.conf.register_opts(DrydockConfig.logging_options, group='logging')
        self.conf.register_opts(DrydockConfig.auth_options, group='authentication')
        self.conf.register_opts(DrydockConfig.plugin_options, group='plugins')
        self.conf.register_opts(DrydockConfig.timeout_options, group='timeouts')



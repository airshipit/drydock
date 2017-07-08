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

"""Single point of entry to generate the sample configuration file.

This module collects all the necessary info from the other modules in this
package. It is assumed that:

* Every other module in this package has a 'list_opts' function which
  returns a dict where:

  * The keys are strings which are the group names.

  * The value of each key is a list of config options for that group.

* The conf package doesn't have further packages with config options.

* This module is only used in the context of sample file generation.

"""
import collections
import importlib
import os
import pkgutil

from oslo_config import cfg

class DrydockConfig(object):
    """
    Initialize all the core options
    """
    # Default options
    options = [
        cfg.IntOpt('poll_interval', default=10, help='Polling interval in seconds for checking subtask or downstream status'),
    ]

    # Logging options
    logging_options = [
        cfg.StrOpt('log_level', default='INFO', help='Global log level for Drydock'),
        cfg.StrOpt('global_logger_name', default='drydock', help='Logger name for the top-level logger'),
        cfg.StrOpt('oobdriver_logger_name', default='${global_logger_name}.oobdriver', help='Logger name for OOB driver logging'),
        cfg.StrOpt('nodedriver_logger_name', default='${global_logger_name}.nodedriver', help='Logger name for Node driver logging'),
        cfg.StrOpt('control_logger_name', default='${global_logger_name}.control', help='Logger name for API server logging'),
    ]

    # API Authentication options
    auth_options = [
        cfg.StrOpt('admin_token', default='bigboss', help='X-Auth-Token value to bypass backend authentication', secret=True),
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
        # TODO Network driver not yet implemented
        cfg.StrOpt('network_driver',
                    default=None,
                    help='Module path string of the Network driver enable'),
    ]

    # Timeouts for various tasks specified in minutes
    timeout_options = [
        cfg.IntOpt('drydock_timeout', default=5, help='Fallback timeout when a specific one is not configured'),
        cfg.IntOpt('create_network_template', default=2, help='Timeout in minutes for creating site network templates'),
        cfg.IntOpt('configure_user_credentials', default=2, help='Timeout in minutes for creating user credentials'),
        cfg.IntOpt('identify_node', default=10, help='Timeout in minutes for initial node identification'),
        cfg.IntOpt('configure_hardware', default=30, help='Timeout in minutes for node commissioning and hardware configuration'),
        cfg.IntOpt('apply_node_networking', default=5, help='Timeout in minutes for configuring node networking'),
        cfg.IntOpt('apply_node_platform', default=5, help='Timeout in minutes for configuring node platform'),
        cfg.IntOpt('deploy_node', default=45, help='Timeout in minutes for deploying a node'),
    ]

    def __init__(self):
        self.conf = cfg.CONF

    def register_options(self):
        self.conf.register_opts(DrydockConfig.options)
        self.conf.register_opts(DrydockConfig.logging_options, group='logging')
        self.conf.register_opts(DrydockConfig.auth_options, group='authentication')
        self.conf.register_opts(DrydockConfig.plugin_options, group='plugins')
        self.conf.register_opts(DrydockConfig.timeout_options, group='timeouts')

IGNORED_MODULES = ('drydock', 'config')
config_mgr = DrydockConfig()

def list_opts():
    opts = {'DEFAULT': DrydockConfig.options,
            'logging': DrydockConfig.logging_options,
            'authentication': DrydockConfig.auth_options,
            'plugins': DrydockConfig.plugin_options,
            'timeouts': DrydockConfig.timeout_options
        }

    package_path = os.path.dirname(os.path.abspath(__file__))
    parent_module = ".".join(__name__.split('.')[:-1])
    module_names = _list_module_names(package_path, parent_module)
    imported_modules = _import_modules(module_names)
    _append_config_options(imported_modules, opts)
    return _tupleize(opts)

def _tupleize(d):
    """Convert a dict of options to the 2-tuple format."""
    return [(key, value) for key, value in d.items()]

def _list_module_names(pkg_path, parent_module):
    module_names = []
    for _, module_name, ispkg in pkgutil.iter_modules(path=[pkg_path]):
        if module_name in IGNORED_MODULES:
            # Skip this module.
            continue
        elif ispkg:
            module_names.extend(_list_module_names(pkg_path + "/" + module_name, parent_module + "." + module_name))
        else:
            module_names.append(parent_module + "." + module_name)
    return module_names

def _import_modules(module_names):
    imported_modules = []
    for module_name in module_names:
        module = importlib.import_module(module_name)
        if hasattr(module, 'list_opts'):
            print("Pulling options from module %s" % module.__name__)
            imported_modules.append(module)
    return imported_modules

def _append_config_options(imported_modules, config_options):
    for module in imported_modules:
        configs = module.list_opts()
        for key, val in configs.items():
            if key not in config_options:
                config_options[key] = val
            else:
                config_options[key].extend(val)

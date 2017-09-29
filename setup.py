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
# drydock_provisioner - A tool to consume a host topology and orchestrate
# and monitor the provisioning of those hosts and execution of bootstrap
# scripts

from setuptools import setup, find_packages

setup(
    name='drydock_provisioner',
    version='0.1a1',
    description='Bootstrapper for Kubernetes infrastructure',
    url='http://github.com/att-comdev/drydock',
    author='AT&T - AIC UCP Developers',
    license='Apache 2.0',
    packages=find_packages(),
    package_data={
        '': ['schemas/*.yaml'],
    },
    entry_points={
        'oslo.config.opts':
        'drydock_provisioner = drydock_provisioner.config:list_opts',
        'oslo.policy.policies':
        'drydock_provisioner = drydock_provisioner.policy:list_policies',
        'console_scripts':
        'drydock = drydock_provisioner.cli.commands:drydock'
    },
)

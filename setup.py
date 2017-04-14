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
# helm_drydock - A tool to consume a host topology and orchestrate
# and monitor the provisioning of those hosts and execution of bootstrap
# scripts
#
# Modular services:
# smelter - 	A service to consume the host topology, will support multiple
#	 			input formats. Initially supports a YAML schema as demonstrated
#				in the examples folder
# tarot -		A service for persisting the host topology and orchestration state
#				and making the data available via API
# cockpit -		The entrypoint API for users to control helm-drydock and query
#				current state
# alchemist -	The core orchestrator
# drivers - 	A tree with all of the plugins that alchemist uses to execute
#				orchestrated tasks
# jabberwocky -	An introspection API that newly provisioned nodes can use to
#				ingest self-data and bootstrap their application deployment process

from setuptools import setup

setup(name='helm_drydock',
      version='0.1a1',
      description='Bootstrapper for Kubernetes infrastructure',
      url='http://github.com/att-comdev/drydock',
      author='Scott Hussey - AT&T',
      author_email='sh8121@att.com',
      license='Apache 2.0',
      packages=['helm_drydock',
                'helm_drydock.model',
                'helm_drydock.ingester',
                'helm_drydock.ingester.plugins',
                'helm_drydock.statemgmt',
                'helm_drydock.orchestrator',
                'helm_drydock.control',
                'helm_drydock.drivers',
                'helm_drydock.drivers.oob'],
      install_requires=[
        'PyYAML',
        'oauth',
        'requests-oauthlib',
        'pyghmi>=1.0.18',
        'netaddr',
        'pecan',
        'webob'
      ],
      dependency_link=[
        'git+https://github.com/maas/python-libmaas.git'
      ]
     )


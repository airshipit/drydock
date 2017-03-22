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
# Models for helm_drydock
#
import logging

from copy import deepcopy

from helm_drydock.orchestrator.enum import SiteStatus
from helm_drydock.orchestrator.enum import NodeStatus

class HardwareProfile(object):

    def __init__(self, **kwargs):
        self.log = logging.Logger('model')

        self.api_version = kwargs.get('apiVersion', '')

        if self.api_version == "v1.0":
            metadata = kwargs.get('metadata', {})
            spec = kwargs.get('spec', {})

            # Need to add validation logic, we'll assume the input is
            # valid for now
            self.name = metadata.get('name', '')
            self.site = metadata.get('region', '')

            self.vendor = spec.get('vendor', None)
            self.generation = spec.get('generation', None)
            self.hw_version = spec.get('hw_version', None)
            self.bios_version = spec.get('bios_version', None)
            self.boot_mode = spec.get('boot_mode', None)
            self.bootstrap_protocol = spec.get('bootstrap_protocol', None)
            self.pxe_interface = spec.get('pxe_interface', None)
            self.devices = []

            device_aliases = spec.get('device_aliases', {})

            pci_devices = device_aliases.get('pci', [])
            scsi_devices = device_aliases.get('scsi', [])

            for d in pci_devices:
                d['bus_type'] = 'pci'
                self.devices.append(
                    HardwareDeviceAlias(self.api_version, **d))

            for d in scsi_devices:
                d['bus_type'] = 'scsi'
                self.devices.append(
                    HardwareDeviceAlias(self.api_version, **d))
        else:
            self.log.error("Unknown API version %s of %s" %
                (self.api_version, self.__class__))
            raise ValueError('Unknown API version of object')

        return

    def get_name(self):
        return self.name
        
    def resolve_alias(self, alias_type, alias):
        selector = {}
        for d in self.devices:
            if d.alias == alias and d.bus_type == alias_type:
                selector['address'] = d.address
                selector['device_type'] = d.type
                return selector

        return None

class HardwareDeviceAlias(object):

    def __init__(self, api_version, **kwargs):
        self.log = logging.Logger('model')

        self.api_version = api_version

        if self.api_version == "v1.0":
            self.bus_type = kwargs.get('bus_type', None)
            self.address = kwargs.get('address', None)
            self.alias = kwargs.get('alias', None)
            self.type = kwargs.get('type', None)
        else:
            self.log.error("Unknown API version %s of %s" %
                (self.api_version, self.__class__))
            raise ValueError('Unknown API version of object')

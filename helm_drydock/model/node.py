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
from helm_drydock.model.hostprofile import HostProfile
from helm_drydock.model import Utils

class BaremetalNode(HostProfile):

    # A BaremetalNode is really nothing more than a physical
    # instantiation of a HostProfile, so they both represent
    # the same set of CIs
    def __init__(self, **kwargs):
        super(BaremetalNode, self).__init__(**kwargs)

        if self.api_version == "v1.0":
            self.addressing = []

            spec = kwargs.get('spec', {})
            addresses = spec.get('addressing', [])

            if len(addresses) == 0:
                raise ValueError('BaremetalNode needs at least' \
                                 ' 1 assigned address')
            for a in addresses:
                assignment = {}
                address = a.get('address', '')
                if address == 'dhcp':
                    assignment['type'] = 'dhcp'
                    assignment['address'] = None
                    assignment['network'] = a.get('network')
                    self.addressing.append(assignment)
                elif address != '':
                    assignment['type'] = 'static'
                    assignment['address'] = a.get('address')
                    assignment['network'] = a.get('network')
                    self.addressing.append(assignment)
                else:
                    self.log.error("Invalid address assignment %s on Node %s" 
                                    % (address, self.name))

        self.build = kwargs.get('build', {})

    def start_build(self):
        if self.build.get('status','') == '':
            self.build['status'] = NodeStatus.Unknown

    def apply_host_profile(self, site):
        return self.apply_inheritance(site)

    # Translate device alises to physical selectors and copy
    # other hardware attributes into this object
    def apply_hardware_profile(self, site):
        self_copy = deepcopy(self)

        if self.hardware_profile is None:
            raise ValueError("Hardware profile not set")

        hw_profile = site.get_hardware_profile(self.hardware_profile)

        for i in self_copy.interfaces:
            for s in i.hardware_slaves:
                selector = hw_profile.resolve_alias("pci", s)
                if selector is None:
                    i.add_selector("name", address=p.device)
                else:
                    i.add_selector("address", address=selector['address'],
                                   dev_type=selector['device_type'])

        for p in self_copy.partitions:
            selector = hw_profile.resolve_alias("scsi", p.device)
            if selector is None:
                p.set_selector("name", address=p.device)
            else:
                p.set_selector("address", address=selector['address'],
                               dev_type=selector['device_type'])


        hardware = {"vendor": getattr(hw_profile, 'vendor', None),
                    "generation": getattr(hw_profile, 'generation', None),
                    "hw_version": getattr(hw_profile, 'hw_version', None),
                    "bios_version": getattr(hw_profile, 'bios_version', None),
                    "boot_mode": getattr(hw_profile, 'boot_mode', None),
                    "bootstrap_protocol": getattr(hw_profile, 
                                                  'bootstrap_protocol',
                                                   None),
                    "pxe_interface": getattr(hw_profile, 'pxe_interface', None)
                    }

        self_copy.hardware = hardware

        return self_copy

    def apply_network_connections(self, site):
        self_copy = deepcopy(self)

        for n in site.network_links:
            for i in self_copy.interfaces:
                i.apply_link_config(n)

        for n in site.networks:
            for i in self_copy.interfaces:
                i.apply_network_config(n)

        for a in self_copy.addressing:
            for i in self_copy.interfaces:
                i.set_network_address(a.get('network'), a.get('address'))

        return self_copy

    def get_interface(self, iface_name):
        for i in self.interfaces:
            if i.device_name == iface_name:
                return i
        return None

    def get_status(self):
        return self.build['status']

    def set_status(self, status):
        if isinstance(status, NodeStatus):
            self.build['status'] = status

    def get_last_build_action(self):
        return self.build.get('last_action', None)

    def set_last_build_action(self, action, result, detail=None):
        last_action = self.build.get('last_action', None)
        if last_action is None:
            self.build['last_action'] = {}
            last_action = self.build['last_action']
            last_action['action'] = action
            last_action['result'] = result
            if detail is not None:
                last_action['detail'] = detail

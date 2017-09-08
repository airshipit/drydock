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
# Models for drydock_provisioner
#
"""Drydock model of a baremetal node."""

from oslo_versionedobjects import fields as ovo_fields

import drydock_provisioner.objects as objects
import drydock_provisioner.objects.hostprofile
import drydock_provisioner.objects.base as base
import drydock_provisioner.objects.fields as hd_fields


@base.DrydockObjectRegistry.register
class BaremetalNode(drydock_provisioner.objects.hostprofile.HostProfile):

    VERSION = '1.0'

    fields = {
        'addressing': ovo_fields.ObjectField('IpAddressAssignmentList'),
        'boot_mac': ovo_fields.StringField(nullable=True),
    }

    # A BaremetalNode is really nothing more than a physical
    # instantiation of a HostProfile, so they both represent
    # the same set of CIs
    def __init__(self, **kwargs):
        super(BaremetalNode, self).__init__(**kwargs)

    # Compile the applied version of this model sourcing referenced
    # data from the passed site design
    def compile_applied_model(self, site_design):
        self.apply_host_profile(site_design)
        self.apply_hardware_profile(site_design)
        self.source = hd_fields.ModelSource.Compiled
        return

    def apply_host_profile(self, site_design):
        self.apply_inheritance(site_design)
        return

    # Translate device alises to physical selectors and copy
    # other hardware attributes into this object
    def apply_hardware_profile(self, site_design):
        if self.hardware_profile is None:
            raise ValueError("Hardware profile not set")

        hw_profile = site_design.get_hardware_profile(self.hardware_profile)

        for i in getattr(self, 'interfaces', []):
            for s in i.get_hw_slaves():
                selector = hw_profile.resolve_alias("pci", s)
                if selector is None:
                    selector = objects.HardwareDeviceSelector()
                    selector.selector_type = 'name'
                    selector.address = s

                i.add_selector(selector)

        for p in getattr(self, 'partitions', []):
            selector = hw_profile.resolve_alias("scsi", p.get_device())
            if selector is None:
                selector = objects.HardwareDeviceSelector()
                selector.selector_type = 'name'
                selector.address = p.get_device()
            p.set_selector(selector)

        return

    def get_applied_interface(self, iface_name):
        for i in getattr(self, 'interfaces', []):
            if i.get_name() == iface_name:
                return i

        return None

    def get_network_address(self, network_name):
        for a in getattr(self, 'addressing', []):
            if a.network == network_name:
                return a.address

        return None

    def find_fs_block_device(self, fs_mount=None):
        if not fs_mount:
            return (None, None)

        if self.volume_groups is not None:
            for vg in self.volume_groups:
                if vg.logical_volumes is not None:
                    for lv in vg.logical_volumes:
                        if lv.mountpoint is not None and lv.mountpoint == fs_mount:
                            return (vg, lv)
        if self.storage_devices is not None:
            for sd in self.storage_devices:
                if sd.partitions is not None:
                    for p in sd.partitions:
                        if p.mountpoint is not None and p.mountpoint == fs_mount:
                            return (sd, p)
        return (None, None)


@base.DrydockObjectRegistry.register
class BaremetalNodeList(base.DrydockObjectListBase, base.DrydockObject):

    VERSION = '1.0'

    fields = {'objects': ovo_fields.ListOfObjectsField('BaremetalNode')}


@base.DrydockObjectRegistry.register
class IpAddressAssignment(base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'type': ovo_fields.StringField(),
        'address': ovo_fields.StringField(nullable=True),
        'network': ovo_fields.StringField(),
    }

    def __init__(self, **kwargs):
        super(IpAddressAssignment, self).__init__(**kwargs)

    # IpAddressAssignment keyed by network
    def get_id(self):
        return self.network


@base.DrydockObjectRegistry.register
class IpAddressAssignmentList(base.DrydockObjectListBase, base.DrydockObject):

    VERSION = '1.0'

    fields = {'objects': ovo_fields.ListOfObjectsField('IpAddressAssignment')}

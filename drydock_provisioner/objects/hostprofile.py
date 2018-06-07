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
"""Models representing host profiles and constituent parts."""

from copy import deepcopy

import oslo_versionedobjects.fields as obj_fields

import drydock_provisioner.objects as objects
import drydock_provisioner.objects.base as base
import drydock_provisioner.objects.fields as hd_fields


@base.DrydockObjectRegistry.register
class HostProfile(base.DrydockPersistentObject, base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'name':
        obj_fields.StringField(nullable=False),
        'site':
        obj_fields.StringField(nullable=False),
        'source':
        hd_fields.ModelSourceField(nullable=False),
        'parent_profile':
        obj_fields.StringField(nullable=True),
        'hardware_profile':
        obj_fields.StringField(nullable=True),
        'oob_type':
        obj_fields.StringField(nullable=True),
        'oob_parameters':
        obj_fields.DictOfStringsField(nullable=True),
        'storage_devices':
        obj_fields.ObjectField('HostStorageDeviceList', nullable=True),
        'volume_groups':
        obj_fields.ObjectField('HostVolumeGroupList', nullable=True),
        'interfaces':
        obj_fields.ObjectField('HostInterfaceList', nullable=True),
        'tags':
        obj_fields.ListOfStringsField(nullable=True),
        'owner_data':
        obj_fields.DictOfStringsField(nullable=True),
        'rack':
        obj_fields.StringField(nullable=True),
        'base_os':
        obj_fields.StringField(nullable=True),
        'image':
        obj_fields.StringField(nullable=True),
        'kernel':
        obj_fields.StringField(nullable=True),
        'kernel_params':
        obj_fields.DictOfStringsField(nullable=True),
        'primary_network':
        obj_fields.StringField(nullable=True),
    }

    def __init__(self, **kwargs):
        super(HostProfile, self).__init__(**kwargs)

    def get_rack(self):
        return self.rack

    # HostProfile is keyed by name
    def get_id(self):
        return self.get_name()

    def get_name(self):
        return self.name

    def has_tag(self, tag):
        if tag in self.tags:
            return True

        return False

    def apply_inheritance(self, site_design):
        # No parent to inherit from, just apply design values
        # and return
        if self.source == hd_fields.ModelSource.Compiled:
            return

        if self.parent_profile is None:
            self.source = hd_fields.ModelSource.Compiled
            return

        parent = site_design.get_host_profile(self.parent_profile)

        if parent is None:
            raise NameError("Cannot find parent profile %s for %s" %
                            (self.design['parent_profile'], self.name))

        parent.apply_inheritance(site_design)

        # First compute inheritance for simple fields
        inheritable_field_list = [
            'hardware_profile', 'oob_type', 'storage_layout',
            'bootdisk_device', 'bootdisk_root_size', 'bootdisk_boot_size',
            'rack', 'base_os', 'image', 'kernel', 'primary_network'
        ]

        # Create applied data from self design values and parent
        # applied values

        for f in inheritable_field_list:
            setattr(
                self, f,
                objects.Utils.apply_field_inheritance(
                    getattr(self, f, None), getattr(parent, f, None)))

        # Now compute inheritance for complex types
        self.oob_parameters = objects.Utils.merge_dicts(
            self.oob_parameters, parent.oob_parameters)

        self.tags = objects.Utils.merge_lists(self.tags, parent.tags)

        self.owner_data = objects.Utils.merge_dicts(self.owner_data,
                                                    parent.owner_data)

        self.kernel_params = objects.Utils.merge_dicts(self.kernel_params,
                                                       parent.kernel_params)

        self.storage_devices = HostStorageDeviceList.from_basic_list(
            HostStorageDevice.merge_lists(self.storage_devices,
                                          parent.storage_devices))

        self.volume_groups = HostVolumeGroupList.from_basic_list(
            HostVolumeGroup.merge_lists(self.volume_groups,
                                        parent.volume_groups))

        self.interfaces = HostInterfaceList.from_basic_list(
            HostInterface.merge_lists(self.interfaces, parent.interfaces))

        self.source = hd_fields.ModelSource.Compiled

        return


@base.DrydockObjectRegistry.register
class HostProfileList(base.DrydockObjectListBase, base.DrydockObject):

    VERSION = '1.0'

    fields = {'objects': obj_fields.ListOfObjectsField('HostProfile')}


@base.DrydockObjectRegistry.register
class HostInterface(base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'device_name':
        obj_fields.StringField(),
        'source':
        hd_fields.ModelSourceField(),
        'network_link':
        obj_fields.StringField(nullable=True),
        'hardware_slaves':
        obj_fields.ListOfStringsField(nullable=True),
        'slave_selectors':
        obj_fields.ObjectField('HardwareDeviceSelectorList', nullable=True),
        'networks':
        obj_fields.ListOfStringsField(nullable=True),
        'sriov':
        obj_fields.BooleanField(default=False),
        # SRIOV virtual functions
        'vf_count':
        obj_fields.IntegerField(nullable=True),
        # SRIOV VF trusted mode
        'trustedmode':
        obj_fields.BooleanField(nullable=True),
    }

    def __init__(self, **kwargs):
        super(HostInterface, self).__init__(**kwargs)

    # HostInterface is keyed by device_name
    def get_id(self):
        return self.get_name()

    def get_name(self):
        return self.device_name

    def get_hw_slaves(self):
        return self.hardware_slaves

    def get_slave_selectors(self):
        return self.slave_selectors

    # Return number of slaves for this interface
    def get_slave_count(self):
        return len(self.hardware_slaves)

    # The device attribute may be hardware alias that translates to a
    # physical device address. If the device attribute does not match an
    # alias, we assume it directly identifies a OS device name. When the
    # apply_hardware_profile method is called on the parent Node of this
    # device, the selector will be decided and applied

    def add_selector(self, slave_selector):
        if self.slave_selectors is None:
            self.slave_selectors = objects.HardwareDeviceSelectorList()

        self.slave_selectors.append(slave_selector)

    """
    Merge two lists of HostInterface models with child_list taking
    priority when conflicts. If a member of child_list has a device_name
    beginning with '!' it indicates that HostInterface should be
    removed from the merged list
    """

    @staticmethod
    def merge_lists(child_list, parent_list):
        if child_list is None:
            return parent_list

        if parent_list is None:
            return child_list

        effective_list = []

        if len(child_list) == 0 and len(parent_list) > 0:
            for p in parent_list:
                pp = deepcopy(p)
                pp.source = hd_fields.ModelSource.Compiled
                effective_list.append(pp)
        elif len(parent_list) == 0 and len(child_list) > 0:
            for i in child_list:
                if i.get_name().startswith('!'):
                    continue
                else:
                    ii = deepcopy(i)
                    ii.source = hd_fields.ModelSource.Compiled
                    effective_list.append(ii)
        elif len(parent_list) > 0 and len(child_list) > 0:
            parent_interfaces = []
            for i in parent_list:
                parent_name = i.get_name()
                parent_interfaces.append(parent_name)
                add = True
                for j in child_list:
                    if j.get_name() == ("!" + parent_name):
                        add = False
                        break
                    elif j.get_name() == parent_name:
                        m = objects.HostInterface()
                        m.device_name = j.get_name()

                        m.network_link = \
                            objects.Utils.apply_field_inheritance(
                                getattr(j, 'network_link', None),
                                getattr(i, 'network_link', None))

                        m.hardware_slaves = objects.Utils.merge_lists(
                            getattr(j, 'hardware_slaves', []),
                            getattr(i, 'hardware_slaves', []))

                        m.networks = objects.Utils.merge_lists(
                            getattr(j, 'networks', []),
                            getattr(i, 'networks', []))

                        m.source = hd_fields.ModelSource.Compiled

                        effective_list.append(m)
                        add = False
                        break

                if add:
                    ii = deepcopy(i)
                    ii.source = hd_fields.ModelSource.Compiled
                    effective_list.append(ii)

            for j in child_list:
                if (j.device_name not in parent_interfaces
                        and not j.get_name().startswith("!")):
                    jj = deepcopy(j)
                    jj.source = hd_fields.ModelSource.Compiled
                    effective_list.append(jj)

        return effective_list


@base.DrydockObjectRegistry.register
class HostInterfaceList(base.DrydockObjectListBase, base.DrydockObject):

    VERSION = '1.0'

    fields = {'objects': obj_fields.ListOfObjectsField('HostInterface')}


@base.DrydockObjectRegistry.register
class HostVolumeGroup(base.DrydockObject):
    """Model representing a host volume group."""

    VERSION = '1.0'

    fields = {
        'name': obj_fields.StringField(),
        'vg_uuid': obj_fields.StringField(nullable=True),
        'logical_volumes': obj_fields.ObjectField(
            'HostVolumeList', nullable=True),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.physical_devices = []

    def get_name(self):
        return self.name

    def get_id(self):
        return self.name

    def add_pv(self, pv):
        self.physical_devices.append(pv)

    def is_sys(self):
        """Check if this is the VG for root and/or boot."""
        for lv in getattr(self, 'logical_volumes', []):
            if lv.is_sys():
                return True
        return False

    @staticmethod
    def merge_lists(child_list, parent_list):
        if child_list is None:
            return parent_list

        if parent_list is None:
            return child_list

        effective_list = []

        if len(child_list) == 0 and len(parent_list) > 0:
            for p in parent_list:
                pp = deepcopy(p)
                pp.source = hd_fields.ModelSource.Compiled
                effective_list.append(pp)
        elif len(parent_list) == 0 and len(child_list) > 0:
            for i in child_list:
                if i.get_name().startswith('!'):
                    continue
                else:
                    ii = deepcopy(i)
                    ii.source = hd_fields.ModelSource.Compiled
                    effective_list.append(ii)
        elif len(parent_list) > 0 and len(child_list) > 0:
            parent_devs = []
            for i in parent_list:
                parent_name = i.get_name()
                parent_devs.append(parent_name)
                add = True
                for j in child_list:
                    if j.get_name() == ("!" + parent_name):
                        add = False
                        break
                    elif j.get_name() == parent_name:
                        p = objects.HostVolumeGroup()
                        p.name = j.get_name()

                        inheritable_field_list = ['vg_uuid']

                        for f in inheritable_field_list:
                            setattr(
                                p, f,
                                objects.Utils.apply_field_inheritance(
                                    getattr(j, f, None), getattr(i, f, None)))

                        p.partitions = HostPartitionList.from_basic_list(
                            HostPartition.merge_lists(
                                getattr(j, 'logical_volumes', None),
                                getattr(i, 'logical_volumes', None)))

                        add = False
                        p.source = hd_fields.ModelSource.Compiled
                        effective_list.append(p)
            if add:
                ii = deepcopy(i)
                ii.source = hd_fields.ModelSource.Compiled
                effective_list.append(ii)

        for j in child_list:
            if (j.get_name() not in parent_devs
                    and not j.get_name().startswith("!")):
                jj = deepcopy(j)
                jj.source = hd_fields.ModelSource.Compiled
                effective_list.append(jj)

        return effective_list


@base.DrydockObjectRegistry.register
class HostVolumeGroupList(base.DrydockObjectListBase, base.DrydockObject):

    VERSION = '1.0'

    fields = {'objects': obj_fields.ListOfObjectsField('HostVolumeGroup')}

    def add_device_to_vg(self, vg_name, device_name):
        for vg in self.objects:
            if vg.name == vg_name:
                vg.add_pv(device_name)
                return

        vg = objects.HostVolumeGroup(name=vg_name)
        vg.add_pv(device_name)
        self.objects.append(vg)
        return


@base.DrydockObjectRegistry.register
class HostStorageDevice(base.DrydockObject):
    """Model representing a host physical storage device."""

    VERSION = '1.0'

    fields = {
        'name': obj_fields.StringField(),
        'volume_group': obj_fields.StringField(nullable=True),
        'labels': obj_fields.DictOfStringsField(nullable=True),
        'partitions': obj_fields.ObjectField(
            'HostPartitionList', nullable=True),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.physical_devices = []

    def get_name(self):
        return self.name

    def get_id(self):
        return self.name

    def add_partition(self, partition):
        self.partitions.append(partition)

    @staticmethod
    def merge_lists(child_list, parent_list):
        if child_list is None:
            return parent_list

        if parent_list is None:
            return child_list

        effective_list = []

        if len(child_list) == 0 and len(parent_list) > 0:
            for p in parent_list:
                pp = deepcopy(p)
                pp.source = hd_fields.ModelSource.Compiled
                effective_list.append(pp)
        elif len(parent_list) == 0 and len(child_list) > 0:
            for i in child_list:
                if i.get_name().startswith('!'):
                    continue
                else:
                    ii = deepcopy(i)
                    ii.source = hd_fields.ModelSource.Compiled
                    effective_list.append(ii)
        elif len(parent_list) > 0 and len(child_list) > 0:
            parent_devs = []
            for i in parent_list:
                parent_name = i.get_name()
                parent_devs.append(parent_name)
                add = True
                for j in child_list:
                    if j.get_name() == ("!" + parent_name):
                        add = False
                        break
                    elif j.get_name() == parent_name:
                        p = objects.HostStorageDevice()
                        p.name = j.get_name()

                        inherit_field_list = ['volume_group']

                        for f in inherit_field_list:
                            setattr(
                                p, f,
                                objects.Utils.apply_field_inheritance(
                                    getattr(j, f, None), getattr(i, f, None)))

                        p.labels = objects.Utils.merge_dicts(
                            getattr(j, 'labels', None),
                            getattr(i, 'labels', None))
                        p.partitions = HostPartitionList.from_basic_list(
                            HostPartition.merge_lists(
                                getattr(j, 'partitions', None),
                                getattr(i, 'partitions', None)))

                        add = False
                        p.source = hd_fields.ModelSource.Compiled
                        effective_list.append(p)
            if add:
                ii = deepcopy(i)
                ii.source = hd_fields.ModelSource.Compiled
                effective_list.append(ii)

        for j in child_list:
            if (j.get_name() not in parent_devs
                    and not j.get_name().startswith("!")):
                jj = deepcopy(j)
                jj.source = hd_fields.ModelSource.Compiled
                effective_list.append(jj)

        return effective_list


@base.DrydockObjectRegistry.register
class HostStorageDeviceList(base.DrydockObjectListBase, base.DrydockObject):
    """Model representing a list of host physical storage devices."""

    VERSION = '1.0'

    fields = {'objects': obj_fields.ListOfObjectsField('HostStorageDevice')}


@base.DrydockObjectRegistry.register
class HostPartition(base.DrydockObject):
    """Model representing a host GPT partition."""

    VERSION = '1.0'

    fields = {
        'name':
        obj_fields.StringField(),
        'source':
        hd_fields.ModelSourceField(),
        'bootable':
        obj_fields.BooleanField(default=False),
        'volume_group':
        obj_fields.StringField(nullable=True),
        'part_uuid':
        obj_fields.UUIDField(nullable=True),
        'size':
        obj_fields.StringField(nullable=True),
        'mountpoint':
        obj_fields.StringField(nullable=True),
        'fstype':
        obj_fields.StringField(nullable=True, default='ext4'),
        'mount_options':
        obj_fields.StringField(nullable=True, default='defaults'),
        'fs_uuid':
        obj_fields.UUIDField(nullable=True),
        'fs_label':
        obj_fields.StringField(nullable=True),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_device(self):
        return self.device

    # HostPartition keyed by name
    def get_id(self):
        return self.get_name()

    def get_name(self):
        return self.name

    def is_sys(self):
        """Check if this is the partition for root and/or boot."""
        if self.mountpoint is not None and self.mountpoint in ['/', '/boot']:
            return True
        return False

    """
    Merge two lists of HostPartition models with child_list taking
    priority when conflicts. If a member of child_list has a name
    beginning with '!' it indicates that HostPartition should be
    removed from the merged list
    """

    @staticmethod
    def merge_lists(child_list, parent_list):
        if child_list is None:
            return parent_list

        if parent_list is None:
            return child_list

        effective_list = []

        if len(child_list) == 0 and len(parent_list) > 0:
            for p in parent_list:
                pp = deepcopy(p)
                pp.source = hd_fields.ModelSource.Compiled
                effective_list.append(pp)
        elif len(parent_list) == 0 and len(child_list) > 0:
            for i in child_list:
                if i.get_name().startswith('!'):
                    continue
                else:
                    ii = deepcopy(i)
                    ii.source = hd_fields.ModelSource.Compiled
                    effective_list.append(ii)
        elif len(parent_list) > 0 and len(child_list) > 0:
            inherit_field_list = [
                "device",
                "part_uuid",
                "size",
                "mountpoint",
                "fstype",
                "mount_options",
                "fs_uuid",
                "fs_label",
                "volume_group",
                "bootable",
            ]
            parent_partitions = []
            for i in parent_list:
                parent_name = i.get_name()
                parent_partitions.append(parent_name)
                add = True
                for j in child_list:
                    if j.get_name() == ("!" + parent_name):
                        add = False
                        break
                    elif j.get_name() == parent_name:
                        p = objects.HostPartition()
                        p.name = j.get_name()

                        for f in inherit_field_list:
                            setattr(
                                p, f,
                                objects.Utils.apply_field_inheritance(
                                    getattr(j, f, None), getattr(i, f, None)))
                        add = False
                        p.source = hd_fields.ModelSource.Compiled
                        effective_list.append(p)
            if add:
                ii = deepcopy(i)
                ii.source = hd_fields.ModelSource.Compiled
                effective_list.append(ii)

        for j in child_list:
            if (j.get_name() not in parent_partitions
                    and not j.get_name().startswith("!")):
                jj = deepcopy(j)
                jj.source = hd_fields.ModelSource.Compiled
                effective_list.append(jj)

        return effective_list


@base.DrydockObjectRegistry.register
class HostPartitionList(base.DrydockObjectListBase, base.DrydockObject):

    VERSION = '1.0'

    fields = {'objects': obj_fields.ListOfObjectsField('HostPartition')}


@base.DrydockObjectRegistry.register
class HostVolume(base.DrydockObject):
    """Model representing a host logical volume."""

    VERSION = '1.0'

    fields = {
        'name':
        obj_fields.StringField(),
        'source':
        hd_fields.ModelSourceField(),
        'lv_uuid':
        obj_fields.UUIDField(nullable=True),
        'size':
        obj_fields.StringField(nullable=True),
        'mountpoint':
        obj_fields.StringField(nullable=True),
        'fstype':
        obj_fields.StringField(nullable=True, default='ext4'),
        'mount_options':
        obj_fields.StringField(nullable=True, default='defaults'),
        'fs_uuid':
        obj_fields.UUIDField(nullable=True),
        'fs_label':
        obj_fields.StringField(nullable=True),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # HostVolume keyed by name
    def get_id(self):
        return self.get_name()

    def get_name(self):
        return self.name

    def is_sys(self):
        """Check if this is the LV for root and/or boot."""
        if self.mountpoint is not None and self.mountpoint in ['/', '/boot']:
            return True
        return False

    """
    Merge two lists of HostVolume models with child_list taking
    priority when conflicts. If a member of child_list has a name
    beginning with '!' it indicates that HostPartition should be
    removed from the merged list
    """

    @staticmethod
    def merge_lists(child_list, parent_list):
        if child_list is None:
            return parent_list

        if parent_list is None:
            return child_list

        effective_list = []

        if len(child_list) == 0 and len(parent_list) > 0:
            for p in parent_list:
                pp = deepcopy(p)
                pp.source = hd_fields.ModelSource.Compiled
                effective_list.append(pp)
        elif len(parent_list) == 0 and len(child_list) > 0:
            for i in child_list:
                if i.get_name().startswith('!'):
                    continue
                else:
                    ii = deepcopy(i)
                    ii.source = hd_fields.ModelSource.Compiled
                    effective_list.append(ii)
        elif len(parent_list) > 0 and len(child_list) > 0:
            inherit_field_list = [
                "lv_uuid",
                "size",
                "mountpoint",
                "fstype",
                "mount_options",
                "fs_uuid",
                "fs_label",
            ]
            parent_volumes = []
            for i in parent_list:
                parent_name = i.get_name()
                parent_volumes.append(parent_name)
                add = True
                for j in child_list:
                    if j.get_name() == ("!" + parent_name):
                        add = False
                        break
                    elif j.get_name() == parent_name:
                        p = objects.HostPartition()
                        p.name = j.get_name()

                        for f in inherit_field_list:
                            setattr(
                                p, f,
                                objects.Utils.apply_field_inheritance(
                                    getattr(j, f, None), getattr(i, f, None)))
                        add = False
                        p.source = hd_fields.ModelSource.Compiled
                        effective_list.append(p)
            if add:
                ii = deepcopy(i)
                ii.source = hd_fields.ModelSource.Compiled
                effective_list.append(ii)

        for j in child_list:
            if (j.get_name() not in parent_volumes
                    and not j.get_name().startswith("!")):
                jj = deepcopy(j)
                jj.source = hd_fields.ModelSource.Compiled
                effective_list.append(jj)

        return effective_list


@base.DrydockObjectRegistry.register
class HostVolumeList(base.DrydockObjectListBase, base.DrydockObject):

    VERSION = '1.0'

    fields = {'objects': obj_fields.ListOfObjectsField('HostVolume')}

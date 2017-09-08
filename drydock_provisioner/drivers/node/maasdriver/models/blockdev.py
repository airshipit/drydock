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
"""API model for MaaS node block device resource."""

import uuid

from . import base as model_base
from . import partition as maas_partition

import drydock_provisioner.error as errors


class BlockDevice(model_base.ResourceBase):

    resource_url = 'nodes/{system_id}/blockdevices/{resource_id}/'
    fields = [
        'resource_id',
        'system_id',
        'name',
        'path',
        'size',
        'type',
        'path',
        'partitions',
        'uuid',
        'filesystem',
        'tags',
        'serial',
        'model',
        'id_path',
        'bootable',
        'available_size',
    ]
    json_fields = [
        'name',
    ]
    """Filesystem dictionary fields:
    mount_point: the mount point on the system directory hierarchy
    fstype: The filesystem format, defaults to ext4
    mount_options: The mount options specified in /etc/fstab, defaults to 'defaults'
    label: The filesystem lab
    uuid: The filesystem uuid
    """

    def __init__(self, api_client, **kwargs):
        super().__init__(api_client, **kwargs)

        if getattr(self, 'resource_id', None) is not None:
            try:
                self.partitions = maas_partition.Partitions(
                    api_client,
                    system_id=self.system_id,
                    device_id=self.resource_id)
                self.partitions.refresh()
            except Exception as ex:
                self.logger.warning(
                    "Could not load partitions on node %s block device %s" %
                    (self.system_id, self.resource_id))
        else:
            self.partitions = None

    def format(self, fstype='ext4', uuid_str=None, label=None):
        """Format this block device with a filesystem.

        :param fstype: String of the filesystem format to use, defaults to ext4
        :param uuid: String of the UUID to assign to the filesystem. One will be
                     generated if this is left as None
        """
        try:
            data = {'fstype': fstype}

            if uuid_str:
                data['uuid'] = str(uuid_str)
            else:
                data['uuid'] = str(uuid.uuid4())

            url = self.interpolate_url()

            self.logger.debug(
                "Formatting device %s on node %s as filesystem: fstype=%s, uuid=%s"
                % (self.name, self.system_id, fstype, uuid))
            resp = self.api_client.post(url, op='format', files=data)

            if not resp.ok:
                raise Exception("MAAS error: %s - %s" % (resp.status_code,
                                                         resp.text))

            self.refresh()
        except Exception as ex:
            msg = "Error: format of device %s on node %s failed: %s" \
                  % (self.name, self.system_id, str(ex))
            self.logger.error(msg)
            raise errors.DriverError(msg)

    def unformat(self):
        """Unformat this block device.

        Will attempt to unmount the device first.
        """
        try:
            self.refresh()
            if self.filesystem is None:
                self.logger.debug(
                    "Device %s not currently formatted, skipping unformat." %
                    (self.name))
                return

            if self.filesystem.get('mount_pount', None) is not None:
                self.unmount()

            url = self.interpolate_url()

            self.logger.debug("Unformatting device %s on node %s" %
                              (self.name, self.system_id))
            resp = self.api_client.post(url, op='unformat')

            if not resp.ok:
                raise Exception("MAAS error: %s - %s" % (resp.status_code,
                                                         resp.text))
            self.refresh()
        except Exception as ex:
            msg = "Error: unformat of device %s on node %s failed: %s" \
                  % (self.name, self.system_id, str(ex))
            self.logger.error(msg)
            raise errors.DriverError(msg)

    def mount(self, mount_point=None, mount_options='defaults'):
        """Mount this block device with a filesystem.

        :param mount_point: The mountpoint on the system
        :param mount_options: fstab style mount options, defaults to 'defaults'
        """
        try:
            if mount_point is None:
                raise errors.DriverError(
                    "Cannot mount a block device on an empty mount point.")

            data = {'mount_point': mount_point, 'mount_options': mount_options}

            url = self.interpolate_url()

            self.logger.debug(
                "Mounting device %s on node %s at mount point %s" %
                (self.resource_id, self.system_id, mount_point))
            resp = self.api_client.post(url, op='mount', files=data)

            if not resp.ok:
                raise Exception("MAAS error: %s - %s" % (resp.status_code,
                                                         resp.text))

            self.refresh()
        except Exception as ex:
            msg = "Error: mount of device %s on node %s failed: %s" \
                  % (self.name, self.system_id, str(ex))
            self.logger.error(msg)
            raise errors.DriverError(msg)

    def unmount(self):
        """Unmount this block device."""
        try:
            self.refresh()
            if self.filesystem is None or self.filesystem.get(
                    'mount_point', None) is None:
                self.logger.debug(
                    "Device %s not currently mounted, skipping unmount." %
                    (self.name))

            url = self.interpolate_url()

            self.logger.debug("Unmounting device %s on node %s" %
                              (self.name, self.system_id))
            resp = self.api_client.post(url, op='unmount')

            if not resp.ok:
                raise Exception("MAAS error: %s - %s" % (resp.status_code,
                                                         resp.text))

            self.refresh()
        except Exception as ex:
            msg = "Error: unmount of device %s on node %s failed: %s" \
                  % (self.name, self.system_id, str(ex))
            self.logger.error(msg)
            raise errors.DriverError(msg)

    def set_bootable(self):
        """Set this disk as the system bootdisk."""
        try:
            url = self.interpolate_url()
            self.logger.debug("Setting device %s on node %s as bootable." %
                              (self.resource_id, self.system_id))
            resp = self.api_client.post(url, op='set_boot_disk')

            if not resp.ok:
                raise Exception("MAAS error: %s - %s" % (resp.status_code,
                                                         resp.text))

            self.refresh()
        except Exception as ex:
            msg = "Error: setting device %s on node %s to boot failed: %s" \
                  % (self.name, self.system_id, str(ex))
            self.logger.error(msg)
            raise errors.DriverError(msg)

    def create_partition(self, partition):
        """Create a partition on this block device.

        :param partition: Instance of models.partition.Partition to be carved out of this block device
        """
        if self.type == 'physical':
            if self.partitions is not None:
                partition = self.partitions.add(partition)
                self.partitions.refresh()
                return self.partitions.select(partition.resource_id)
            else:
                msg = "Error: could not access device %s partition list" % self.name
                self.logger.error(msg)
                raise errors.DriverError(msg)
        else:
            msg = "Error: cannot partition non-physical device %s." % (
                self.name)
            self.logger.error(msg)
            raise errors.DriverError(msg)

    def delete_partition(self, partition_id):
        if self.partitions is not None:
            part = self.partitions.select(partition_id)
            if part is not None:
                part.delete()
                self.refresh()

    def clear_partitions(self):
        for p in getattr(self, 'partitions', []):
            p.delete()
        self.refresh()

    @classmethod
    def from_dict(cls, api_client, obj_dict):
        """Instantiate this model from a dictionary.

        Because MaaS decides to replace the resource ids with the
        representation of the resource, we must reverse it for a true
        representation of the block device
        """
        refined_dict = {k: obj_dict.get(k, None) for k in cls.fields}
        if 'id' in obj_dict.keys():
            refined_dict['resource_id'] = obj_dict.get('id')

        i = cls(api_client, **refined_dict)
        return i


class BlockDevices(model_base.ResourceCollectionBase):

    collection_url = 'nodes/{system_id}/blockdevices/'
    collection_resource = BlockDevice

    def __init__(self, api_client, **kwargs):
        super().__init__(api_client)
        self.system_id = kwargs.get('system_id', None)

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
"""API model for MaaS node storage partition resource."""

import uuid

from . import base as model_base

import drydock_provisioner.error as errors


class Partition(model_base.ResourceBase):

    resource_url = 'nodes/{system_id}/blockdevices/{device_id}/partition/{resource_id}'
    fields = [
        'resource_id',
        'system_id',
        'device_id',
        'name',
        'path',
        'size',
        'type',
        'uuid',
        'filesystem',
        'bootable',
    ]
    json_fields = [
        'size',
        'uuid',
        'bootable',
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

    def format(self, fstype='ext4', uuid_str=None, fs_label=None):
        """Format this partition with a filesystem.

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

            if fs_label is not None:
                data['label'] = fs_label

            url = self.interpolate_url()

            self.logger.debug(
                "Formatting device %s on node %s as filesystem: %s" %
                (self.name, self.system_id, data))
            resp = self.api_client.post(url, op='format', files=data)

            if not resp.ok:
                raise Exception("MAAS error: %s - %s" %
                                (resp.status_code, resp.text))

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
                raise Exception("MAAS error: %s - %s" %
                                (resp.status_code, resp.text))
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
                raise Exception("MAAS error: %s - %s" %
                                (resp.status_code, resp.text))
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
                raise Exception("MAAS error: %s - %s" %
                                (resp.status_code, resp.text))
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
                raise Exception("MAAS error: %s - %s" %
                                (resp.status_code, resp.text))
            self.refresh()
        except Exception as ex:
            msg = "Error: setting device %s on node %s to boot failed: %s" \
                  % (self.name, self.system_id, str(ex))
            self.logger.error(msg)
            raise errors.DriverError(msg)

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


class Partitions(model_base.ResourceCollectionBase):

    collection_url = 'nodes/{system_id}/blockdevices/{device_id}/partitions/'
    collection_resource = Partition

    def __init__(self, api_client, **kwargs):
        super().__init__(api_client)
        self.system_id = kwargs.get('system_id', None)
        self.device_id = kwargs.get('device_id', None)

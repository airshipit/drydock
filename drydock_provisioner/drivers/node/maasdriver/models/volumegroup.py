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
"""API model for MaaS node volume group resource."""

import uuid

from . import base as model_base

import drydock_provisioner.error as errors


class VolumeGroup(model_base.ResourceBase):

    resource_url = 'nodes/{system_id}/volume-group/{resource_id}/'
    fields = [
        'resource_id',
        'system_id',
        'name',
        'size',
        'available_size',
        'uuid',
        'logical_volumes',
        'block_devices',
        'partitions',
    ]
    json_fields = [
        'name',
        'size',
        'uuid',
        'block_devices',
        'partitions',
    ]

    def create_lv(self, name=None, uuid_str=None, size=None):
        """Create a logical volume in this volume group.

        :param name: Name of the logical volume
        :param uuid_str: A UUID4-format string specifying the LV uuid. Will be generated if left as None
        :param size: The size of the logical volume
        """
        try:
            if name is None or size is None:
                raise Exception(
                    "Cannot create logical volume without specified name and size"
                )

            if uuid_str is None:
                uuid_str = str(uuid.uuid4())

            data = {'name': name, 'uuid': uuid_str, 'size': size}

            self.logger.debug(
                "Creating logical volume %s in VG %s on node %s" %
                (name, self.name, self.system_id))

            url = self.interpolate_url()

            resp = self.api_client.post(
                url, op='create_logical_volume', files=data)

            if not resp.ok:
                raise Exception("MAAS error - %s - %s" % (resp.status_code,
                                                          resp.txt))

            res = resp.json()
            if 'id' in res:
                return res['id']

        except Exception as ex:
            msg = "Error: Could not create logical volume: %s" % str(ex)
            self.logger.error(msg)
            raise errors.DriverError(msg)

    def delete_lv(self, lv_id=None, lv_name=None):
        """Delete a logical volume from this volume group.

        :param lv_id: Resource ID of the logical volume
        :param lv_name: Name of the logical volume, only referenced if no lv_id is specified
        """
        try:
            self.refresh()
            if self.logical_volumes is not None:
                if lv_id and lv_id in self.logical_volumes.values():
                    target_lv = lv_id
                elif lv_name and lv_name in self.logical_volumes:
                    target_lv = self.logical_volumes[lv_name]
                else:
                    raise Exception(
                        "lv_id %s and lv_name %s not found in VG %s" %
                        (lv_id, lv_name, self.name))

                url = self.interpolate_url()

                resp = self.api_client.post(
                    url, op='delete_logical_volume', files={
                        'id': target_lv
                    })

                if not resp.ok:
                    raise Exception("MAAS error - %s - %s" % (resp.status_code,
                                                              resp.text))
            else:
                raise Exception("VG %s has no logical volumes" % self.name)
        except Exception as ex:
            msg = "Error: Could not delete logical volume: %s" % str(ex)
            self.logger.error(msg)
            raise errors.DriverError(msg)

    def delete(self):
        """Delete this volume group.

        Override the default delete so that logical volumes can be
        removed first.
        """
        for lv in self.logical_volumes:
            self.delete_lv(lv_name=lv)

        super().delete()

    @classmethod
    def from_dict(cls, api_client, obj_dict):
        """Instantiate this model from a dictionary.

        Because MaaS decides to replace the resource ids with the
        representation of the resource, we must reverse it for a true
        representation of the block device
        """
        refined_dict = {k: obj_dict.get(k, None) for k in cls.fields}
        if 'id' in obj_dict:
            refined_dict['resource_id'] = obj_dict.get('id')

        if 'logical_volumes' in refined_dict and isinstance(
                refined_dict.get('logical_volumes'), list):
            lvs = {}
            for v in refined_dict.get('logical_volumes'):
                lvs[v.get('name')] = v.get('id')
            refined_dict['logical_volumes'] = lvs

        i = cls(api_client, **refined_dict)
        return i


class VolumeGroups(model_base.ResourceCollectionBase):

    collection_url = 'nodes/{system_id}/volume-groups/'
    collection_resource = VolumeGroup

    def __init__(self, api_client, **kwargs):
        super().__init__(api_client)
        self.system_id = kwargs.get('system_id', None)

    def add(self, res):
        res = super().add(res)
        res.system_id = self.system_id
        return res

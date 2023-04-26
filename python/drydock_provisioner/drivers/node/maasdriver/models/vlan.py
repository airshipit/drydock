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
"""Models representing MaaS VLAN resources."""

import drydock_provisioner.drivers.node.maasdriver.models.base as model_base
from drydock_provisioner.drivers.node.maasdriver.errors import RackControllerConflict


class Vlan(model_base.ResourceBase):

    resource_url = 'fabrics/{fabric_id}/vlans/{api_id}/'
    fields = [
        'resource_id',
        'name',
        'description',
        'vid',
        'fabric_id',
        'dhcp_on',
        'mtu',
        'primary_rack',
        'secondary_rack',
        'relay_vlan',
    ]
    json_fields = [
        'name',
        'description',
        'vid',
        'dhcp_on',
        'mtu',
        'primary_rack',
        'secondary_rack',
        'relay_vlan',
    ]

    def __init__(self, api_client, **kwargs):
        super(Vlan, self).__init__(api_client, **kwargs)

        if self.vid is None:
            self.vid = 0

        # the MaaS API decided that the URL endpoint for VLANs should use
        # the VLAN tag (vid) rather than the resource ID. So to update the
        # vid, we have to keep two copies so that the resource_url
        # is accurate for updates
        self.api_id = self.vid

    def update(self):
        super(Vlan, self).update()

        self.api_id = self.vid

    def set_vid(self, new_vid):
        if new_vid is None:
            self.vid = 0
        else:
            self.vid = int(new_vid)

    def add_rack_controller(self, rack_id):
        """Add a rack controller that manages DHCP on this VLAN.

        Whichever of primary_rack or secondary_rack, in that order,
        is not set - set to ``rack_id``. If both are already set
        raise RackControllerConflict exception.
        """
        if not self.primary_rack or self.primary_rack == rack_id:
            self.logger.debug("Setting primary DHCP controller %s on VLAN %s",
                              rack_id, self.resource_id)
            self.primary_rack = rack_id
        elif not self.secondary_rack or self.secondary_rack == rack_id:
            self.logger.debug(
                "Setting secondary DHCP controller %s on VLAN %s.", rack_id,
                self.resource_id)
            self.secondary_rack = rack_id
        else:
            raise RackControllerConflict(
                "Both primary and secondary rack controllers already set.")

    def reset_dhcp_mgmt(self, commit=False):
        """Reset the DHCP control for this VLAN.

        Reset the settings in the model impacting DHCP control on this
        VLAN. Only commit these changes to the MAAS API if ``commit`` is
        True.

        :param bool commit: Whether to commit reset to MAAS API
        """
        self.logger.debug("Resetting DHCP control on VLAN %s.",
                          self.resource_id)
        self.relay_vlan = None
        self.dhcp_on = False
        self.primary_rack = None
        self.secondary_rack = None

        if commit:
            self.update()

    def set_dhcp_relay(self, relay_vlan_id):
        self.relay_vlan = relay_vlan_id
        self.update()

    @classmethod
    def from_dict(cls, api_client, obj_dict):
        """
        Because MaaS decides to replace the relay_vlan id with the
        representation of the VLAN, we must reverse it for a true
        representation of the resource
        """
        refined_dict = {k: obj_dict.get(k, None) for k in cls.fields}
        if 'id' in obj_dict.keys():
            refined_dict['resource_id'] = obj_dict.get('id')

        if isinstance(refined_dict.get('relay_vlan', None), dict):
            refined_dict['relay_vlan'] = refined_dict['relay_vlan']['id']

        i = cls(api_client, **refined_dict)
        return i


class Vlans(model_base.ResourceCollectionBase):

    collection_url = 'fabrics/{fabric_id}/vlans/'
    collection_resource = Vlan

    def __init__(self, api_client, **kwargs):
        super(Vlans, self).__init__(api_client)

        self.fabric_id = kwargs.get('fabric_id', None)

    """
    Create a new resource in this collection in MaaS
    def add(self, res):
        #MAAS API doesn't support all attributes in POST, so create and
        # then promptly update via PUT

        min_fields = {
            'name':   res.name,
            'description':  getattr(res, 'description', None),
        }

        if getattr(res, 'vid', None) is None:
            min_fields['vid'] = 0
        else:
            min_fields['vid'] = res.vid

        url = self.interpolate_url()
        resp = self.api_client.post(url, files=min_fields)

        # Check on initial POST creation
        if resp.status_code == 200:
            resp_json = resp.json()
            res.id = resp_json.get('id')
            # Submit PUT for additonal fields
            res.update()
            return res

        raise errors.DriverError("Failed updating MAAS url %s - return code %s\n%s"
                % (url, resp.status_code, resp.text))
    """

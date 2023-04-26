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
"""Model for a server rack in a site."""

import oslo_versionedobjects.fields as obj_fields

import drydock_provisioner.objects.base as base
import drydock_provisioner.objects.fields as hd_fields


@base.DrydockObjectRegistry.register
class Rack(base.DrydockPersistentObject, base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'name': obj_fields.StringField(nullable=False),
        'site': obj_fields.StringField(nullable=False),
        'source': hd_fields.ModelSourceField(nullable=False),
        'tor_switches': obj_fields.ObjectField('TorSwitchList',
                                               nullable=False),
        'location': obj_fields.DictOfStringsField(nullable=False),
        'local_networks': obj_fields.ListOfStringsField(nullable=True),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_id(self):
        return self.get_name()

    def get_name(self):
        return self.name


@base.DrydockObjectRegistry.register
class RackList(base.DrydockObjectListBase, base.DrydockObject):

    VERSION = '1.0'

    fields = {'objects': obj_fields.ListOfObjectsField('Rack')}


@base.DrydockObjectRegistry.register
class TorSwitch(base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'switch_name': obj_fields.StringField(),
        'mgmt_ip': obj_fields.StringField(nullable=True),
        'sdn_api_uri': obj_fields.StringField(nullable=True),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # HostInterface is keyed by device_name
    def get_id(self):
        return self.get_name()

    def get_name(self):
        return self.switch_name


@base.DrydockObjectRegistry.register
class TorSwitchList(base.DrydockObjectListBase, base.DrydockObject):

    VERSION = '1.0'

    fields = {'objects': obj_fields.ListOfObjectsField('TorSwitch')}

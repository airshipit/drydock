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
from copy import deepcopy

from oslo_versionedobjects import fields as ovo_fields

import drydock_provisioner.objects as objects
import drydock_provisioner.objects.base as base
import drydock_provisioner.objects.fields as hd_fields


@base.DrydockObjectRegistry.register
class HardwareProfile(base.DrydockPersistentObject, base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'name':
        ovo_fields.StringField(),
        'source':
        hd_fields.ModelSourceField(),
        'site':
        ovo_fields.StringField(),
        'vendor':
        ovo_fields.StringField(nullable=True),
        'generation':
        ovo_fields.StringField(nullable=True),
        'hw_version':
        ovo_fields.StringField(nullable=True),
        'bios_version':
        ovo_fields.StringField(nullable=True),
        'boot_mode':
        ovo_fields.StringField(nullable=True),
        'bootstrap_protocol':
        ovo_fields.StringField(nullable=True),
        'pxe_interface':
        ovo_fields.StringField(nullable=True),
        'devices':
        ovo_fields.ObjectField('HardwareDeviceAliasList', nullable=True),
    }

    def __init__(self, **kwargs):
        super(HardwareProfile, self).__init__(**kwargs)

        return

    # HardwareProfile keyed on name
    def get_id(self):
        return self.get_name()

    def get_name(self):
        return self.name

    def resolve_alias(self, alias_type, alias):
        for d in self.devices:
            if d.alias == alias and d.bus_type == alias_type:
                selector = objects.HardwareDeviceSelector()
                selector.selector_type = "address"
                selector.address = d.address
                selector.device_type = d.dev_type
                return selector

        return None


@base.DrydockObjectRegistry.register
class HardwareProfileList(base.DrydockObjectListBase, base.DrydockObject):

    VERSION = '1.0'

    fields = {'objects': ovo_fields.ListOfObjectsField('HardwareProfile')}


@base.DrydockObjectRegistry.register
class HardwareDeviceAlias(base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'alias': ovo_fields.StringField(),
        'source': hd_fields.ModelSourceField(),
        'address': ovo_fields.StringField(),
        'bus_type': ovo_fields.StringField(),
        'dev_type': ovo_fields.StringField(nullable=True),
    }

    def __init__(self, **kwargs):
        super(HardwareDeviceAlias, self).__init__(**kwargs)

    # HardwareDeviceAlias keyed on alias
    def get_id(self):
        return self.alias


@base.DrydockObjectRegistry.register
class HardwareDeviceAliasList(base.DrydockObjectListBase, base.DrydockObject):

    VERSION = '1.0'

    fields = {'objects': ovo_fields.ListOfObjectsField('HardwareDeviceAlias')}


@base.DrydockObjectRegistry.register
class HardwareDeviceSelector(base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'selector_type': ovo_fields.StringField(),
        'address': ovo_fields.StringField(),
        'device_type': ovo_fields.StringField()
    }

    def __init__(self, **kwargs):
        super(HardwareDeviceSelector, self).__init__(**kwargs)


@base.DrydockObjectRegistry.register
class HardwareDeviceSelectorList(base.DrydockObjectListBase,
                                 base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'objects': ovo_fields.ListOfObjectsField('HardwareDeviceSelector')
    }

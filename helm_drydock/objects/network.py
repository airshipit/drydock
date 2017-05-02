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

import oslo_versionedobjects.fields as ovo_fields

import helm_drydock.objects as objects
import helm_drydock.objects.base as base
import helm_drydock.objects.fields as hd_fields

@base.DrydockObjectRegistry.register
class NetworkLink(base.DrydockPersistentObject, base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'name':             ovo_fields.StringField(),
        'site':             ovo_fields.StringField(),
        'bonding_mode':     hd_fields.NetworkLinkBondingModeField(
                                        default=hd_fields.NetworkLinkBondingMode.Disabled),
        'bonding_xmit_hash':    ovo_fields.StringField(nullable=True),
        'bonding_peer_rate':    ovo_fields.StringField(nullable=True),
        'bonding_mon_rate':     ovo_fields.IntegerField(nullable=True),
        'bonding_up_delay':     ovo_fields.IntegerField(nullable=True),
        'bonding_down_delay':   ovo_fields.IntegerField(nullable=True),
        'mtu':              ovo_fields.IntegerField(default=1500),
        'linkspeed':        ovo_fields.StringField(default='auto'),
        'trunk_mode':       hd_fields.NetworkLinkTrunkingModeField(
                                        default=hd_fields.NetworkLinkTrunkingMode.Disabled),
        'native_network':   ovo_fields.StringField(nullable=True),
    }

    def __init__(self, **kwargs):
        super(NetworkLink, self).__init__(**kwargs)

    # NetworkLink keyed by name
    def get_id(self):
        return self.get_name()

    def get_name(self):
        return self.name


@base.DrydockObjectRegistry.register
class NetworkLinkList(base.DrydockObjectListBase, base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'objects':  ovo_fields.ListOfObjectsField('NetworkLink'),
    }


@base.DrydockObjectRegistry.register
class Network(base.DrydockPersistentObject, base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'name':     ovo_fields.StringField(),
        'site':     ovo_fields.StringField(),
        'cidr':     ovo_fields.StringField(),
        'allocation_strategy':  ovo_fields.StringField(),
        'vlan_id':  ovo_fields.StringField(nullable=True),
        'mtu':      ovo_fields.IntegerField(nullable=True),
        'dns_domain':   ovo_fields.StringField(nullable=True),
        'dns_servers':  ovo_fields.StringField(nullable=True),
        'ranges':   ovo_fields.ListOfDictOfNullableStringsField(),
        'routes':   ovo_fields.ListOfDictOfNullableStringsField(),
    }

    def __init__(self, **kwargs):
        super(Network, self).__init__(**kwargs)

    # Network keyed on name
    def get_id(self):
        return self.get_name()
        
    def get_name(self):
        return self.name


@base.DrydockObjectRegistry.register
class NetworkList(base.DrydockObjectListBase, base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'objects':  ovo_fields.ListOfObjectsField('Network'),
    }

    def __init__(self, **kwargs):
        super(NetworkList, self).__init__(**kwargs)
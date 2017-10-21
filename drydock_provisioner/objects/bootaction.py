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
"""Object models for BootActions."""

import oslo_versionedobjects.fields as ovo_fields

import drydock_provisioner.objects.base as base
import drydock_provisioner.objects.fields as hd_fields


@base.DrydockObjectRegistry.register
class BootAction(base.DrydockPersistentObject, base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'name':
        ovo_fields.StringField(),
        'source':
        hd_fields.ModelSourceField(nullable=False),
        'asset_list':
        ovo_fields.ObjectField('BootActionAssetList', nullable=False),
        'node_filter':
        ovo_fields.ObjectField('NodeFilterSet', nullable=True),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # NetworkLink keyed by name
    def get_id(self):
        return self.get_name()

    def get_name(self):
        return self.name


@base.DrydockObjectRegistry.register
class BootActionList(base.DrydockObjectListBase, base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'objects': ovo_fields.ListOfObjectsField('BootAction'),
    }


@base.DrydockObjectRegistry.register
class BootActionAsset(base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'type': ovo_fields.StringField(nullable=True),
        'path': ovo_fields.StringField(nullable=True),
        'location': ovo_fields.StringField(nullable=True),
        'data': ovo_fields.StringField(nullable=True),
        'location_pipeline': ovo_fields.ListOfStringsField(nullable=True),
        'data_pipeline': ovo_fields.ListOfStringsField(nullable=True),
        'permissions': ovo_fields.IntegerField(nullable=True),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


@base.DrydockObjectRegistry.register
class BootActionAssetList(base.DrydockObjectListBase, base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'objects': ovo_fields.ListOfObjectsField('BootActionAsset'),
    }


@base.DrydockObjectRegistry.register
class NodeFilterSet(base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'filter_set_type': ovo_fields.StringField(nullable=False),
        'filter_set': ovo_fields.ListOfObjectsField('NodeFilter'),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


@base.DrydockObjectRegistry.register
class NodeFilter(base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'filter_type': ovo_fields.StringField(nullable=False),
        'node_names': ovo_fields.ListOfStringsField(nullable=True),
        'node_tags': ovo_fields.ListOfStringsField(nullable=True),
        'node_labels': ovo_fields.DictOfStringsField(nullable=True),
        'rack_names': ovo_fields.ListOfStringsField(nullable=True),
        'rack_labels': ovo_fields.DictOfStringsField(nullable=True),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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
from oslo_versionedobjects import fields as ovo_fields

import drydock_provisioner.objects as objects
import drydock_provisioner.objects.base as base
import drydock_provisioner.objects.fields as hd_fields

@base.DrydockObjectRegistry.register
class PromenadeConfig(base.DrydockPersistentObject, base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'target': ovo_fields.StringField(),
        'name': ovo_fields.StringField(nullable=True),
        'kind': ovo_fields.StringField(),
        'document': ovo_fields.StringField(),
    }

    def __init__(self, **kwargs):
        super(PromenadeConfig, self).__init__(**kwargs)

        return

    # HardwareProfile keyed on name
    def get_id(self):
        return self.get_name()

    def get_name(self):
        return self.name

@base.DrydockObjectRegistry.register
class PromenadeConfigList(base.DrydockObjectListBase, base.DrydockObject):

    VERSION = '1.0'

    fields = {
             'objects':  ovo_fields.ListOfObjectsField('PromenadeConfig'),
             }

    def select_for_target(self, target):
        """
        Select all promenade configs destined for the target

        :param string target: Target to search documents for
        """

        return [x for x in self.objects if x.target == target]


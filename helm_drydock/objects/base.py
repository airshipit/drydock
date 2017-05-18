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

from oslo_versionedobjects import base
from oslo_versionedobjects import fields as obj_fields

import helm_drydock.objects as objects

class DrydockObjectRegistry(base.VersionedObjectRegistry):
    
    # Steal this from Cinder to bring all registered objects
    # into the helm_drydock.objects namespace

    def registration_hook(self, cls, index):
        setattr(objects, cls.obj_name(), cls)

class DrydockObject(base.VersionedObject):

    VERSION = '1.0'

    OBJ_PROJECT_NAMESPACE = 'helm_drydock.objects'

    # Return None for undefined attributes
    def obj_load_attr(self, attrname):
        if attrname in self.fields.keys():
            setattr(self, attrname, None)
        else:
            raise ValueError("Unknown field %s" % (attrname))

class DrydockPersistentObject(base.VersionedObject):

    fields = {
        'created_at': obj_fields.DateTimeField(nullable=False),
        'created_by': obj_fields.StringField(nullable=False),
        'updated_at': obj_fields.DateTimeField(nullable=True),
        'updated_by': obj_fields.StringField(nullable=True),
    }

class DrydockObjectListBase(base.ObjectListBase):
    
    def __init__(self, **kwargs):
        super(DrydockObjectListBase, self).__init__(**kwargs)

    def append(self, obj):
        self.objects.append(obj)

    def replace_by_id(self, obj):
        i = 0;
        while i < len(self.objects):
            if self.objects[i].get_id() == obj.get_id():
                objects[i] = obj
                return True
            i = i + 1

        return False

    @classmethod
    def from_basic_list(cls, obj_list):
        model_list = cls()

        for o in obj_list:
            model_list.append(o)

        return model_list

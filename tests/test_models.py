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

import pytest

import helm_drydock.objects as objects
from helm_drydock.objects import fields

class TestClass(object):

    def test_hardwareprofile(self):
        objects.register_all()

        model_attr = {
            'versioned_object.namespace':            'helm_drydock.objects',
            'versioned_object.name':                 'HardwareProfile',
            'versioned_object.version':              '1.0',
            'versioned_object.data': {
                'name':                 'server',
                'source':               fields.ModelSource.Designed,
                'site':                 'test_site',
                'vendor':               'Acme',
                'generation':           '9',
                'hw_version':           '3',
                'bios_version':         '2.1.1',
                'boot_mode':            'bios',
                'bootstrap_protocol':   'pxe',
                'pxe_interface':        '0',
                'devices':  {
                    'versioned_object.namespace':    'helm_drydock.objects',
                    'versioned_object.name':         'HardwareDeviceAliasList',
                    'versioned_object.version':      '1.0',
                    'versioned_object.data': {
                        'objects': [
                            {
                                'versioned_object.namespace':    'helm_drydock.objects',
                                'versioned_object.name':         'HardwareDeviceAlias',
                                'versioned_object.version':      '1.0',
                                'versioned_object.data': {
                                    'alias':    'nic',
                                    'source':   fields.ModelSource.Designed,
                                    'address':  '0000:00:03.0',
                                    'bus_type': 'pci',
                                    'dev_type': '82540EM Gigabit Ethernet Controller',
                                }
                            },
                            {
                                'versioned_object.namespace':    'helm_drydock.objects',
                                'versioned_object.name':         'HardwareDeviceAlias',
                                'versioned_object.version':      '1.0',
                                'versioned_object.data': {
                                    'alias':    'bootdisk',
                                    'source':   fields.ModelSource.Designed,
                                    'address':  '2:0.0.0',
                                    'bus_type': 'scsi',
                                    'dev_type': 'SSD',
                                }
                            },
                        ]

                    }
                }
            }
        }

        hwprofile = objects.HardwareProfile.obj_from_primitive(model_attr)

        assert getattr(hwprofile, 'bootstrap_protocol') == 'pxe'
        
        hwprofile.bootstrap_protocol = 'network'

        assert 'bootstrap_protocol' in hwprofile.obj_what_changed()
        assert 'bios_version' not in hwprofile.obj_what_changed()


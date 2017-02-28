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
import yaml
from helm_drydock.model import HardwareProfile

class TestClass(object):

    def setup_method(self, method):
        print("Running test {0}".format(method.__name__))

    def test_hardwareprofile(self):
        yaml_snippet = ("---\n"
                        "apiVersion: 'v1.0'\n"
                        "kind: HardwareProfile\n"
                        "metadata:\n"
                        "  name: HPGen8v3\n"
                        "  region: sitename\n"
                        "  date: 17-FEB-2017\n"
                        "  name: Sample hardware definition\n"
                        "  author: Scott Hussey\n"
                        "spec:\n"
                        "  # Vendor of the server chassis\n"
                        "  vendor: HP\n"
                        "  # Generation of the chassis model\n"
                        "  generation: '8'\n"
                        "  # Version of the chassis model within its generation - not version of the hardware definition\n"
                        "  hw_version: '3'\n"
                        "  # The certified version of the chassis BIOS\n"
                        "  bios_version: '2.2.3'\n"
                        "  # Mode of the default boot of hardware - bios, uefi\n"
                        "  boot_mode: bios\n"
                        "  # Protocol of boot of the hardware - pxe, usb, hdd\n"
                        "  bootstrap_protocol: pxe\n"
                        "  # Which interface to use for network booting within the OOB manager, not OS device\n"
                        "  pxe_interface: 0\n"
                        "  # Map hardware addresses to aliases/roles to allow a mix of hardware configs\n"
                        "  # in a site to result in a consistent configuration\n"
                        "  device_aliases:\n"
                        "    pci:\n"
                        "    - address: pci@0000:00:03.0\n"
                        "      alias: prim_nic01\n"
                        "      # type could identify expected hardware - used for hardware manifest validation\n"
                        "      type: '82540EM Gigabit Ethernet Controller'\n"
                        "    - address: pci@0000:00:04.0\n"
                        "      alias: prim_nic02\n"
                        "      type: '82540EM Gigabit Ethernet Controller'\n"
                        "    scsi:\n"
                        "    - address: scsi@2:0.0.0\n"
                        "      alias: primary_boot\n"
                        "      type: 'VBOX HARDDISK'\n")

        hw_profile = yaml.load(yaml_snippet)
        hw_profile_model = HardwareProfile(**hw_profile)

        assert hasattr(hw_profile_model, 'bootstrap_protocol')


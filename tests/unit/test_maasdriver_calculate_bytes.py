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
'''Tests for the maasdriver calculate_bytes routine.'''

import pytest
import math

from drydock_provisioner import error

from drydock_provisioner.drivers.node.maasdriver.actions.node import ApplyNodeStorage
from drydock_provisioner.drivers.node.maasdriver.models.blockdev import BlockDevice
from drydock_provisioner.drivers.node.maasdriver.models.volumegroup import VolumeGroup


class TestCalculateBytes():
    def test_calculate_m_label(self):
        '''Convert megabyte labels to x * 10^6 bytes.'''
        size_str = '15m'
        drive_size = 20 * 1000 * 1000

        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(
            size_str=size_str, context=drive)

        assert calc_size == 15 * 1000 * 1000

    def test_calculate_mb_label(self):
        '''Convert megabyte labels to x * 10^6 bytes.'''
        size_str = '15mb'
        drive_size = 20 * 1000 * 1000
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(
            size_str=size_str, context=drive)

        assert calc_size == 15 * 1000 * 1000

    def test_calculate_M_label(self):
        '''Convert megabyte labels to x * 10^6 bytes.'''
        size_str = '15M'
        drive_size = 20 * 1000 * 1000
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(
            size_str=size_str, context=drive)

        assert calc_size == 15 * 1000 * 1000

    def test_calculate_MB_label(self):
        '''Convert megabyte labels to x * 10^6 bytes.'''
        size_str = '15MB'
        drive_size = 20 * 1000 * 1000
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(
            size_str=size_str, context=drive)

        assert calc_size == 15 * 1000 * 1000

    def test_calculate_g_label(self):
        '''Convert gigabyte labels to x * 10^9 bytes.'''
        size_str = '15g'
        drive_size = 20 * 1000 * 1000 * 1000
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(
            size_str=size_str, context=drive)

        assert calc_size == 15 * 1000 * 1000 * 1000

    def test_calculate_gb_label(self):
        '''Convert gigabyte labels to x * 10^9 bytes.'''
        size_str = '15gb'
        drive_size = 20 * 1000 * 1000 * 1000
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(
            size_str=size_str, context=drive)

        assert calc_size == 15 * 1000 * 1000 * 1000

    def test_calculate_G_label(self):
        '''Convert gigabyte labels to x * 10^9 bytes.'''
        size_str = '15G'
        drive_size = 20 * 1000 * 1000 * 1000
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(
            size_str=size_str, context=drive)

        assert calc_size == 15 * 1000 * 1000 * 1000

    def test_calculate_GB_label(self):
        '''Convert gigabyte labels to x * 10^9 bytes.'''
        size_str = '15GB'
        drive_size = 20 * 1000 * 1000 * 1000
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(
            size_str=size_str, context=drive)

        assert calc_size == 15 * 1000 * 1000 * 1000

    def test_calculate_t_label(self):
        '''Convert terabyte labels to x * 10^12 bytes.'''
        size_str = '15t'
        drive_size = 20 * 1000 * 1000 * 1000 * 1000
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(
            size_str=size_str, context=drive)

        assert calc_size == 15 * 1000 * 1000 * 1000 * 1000

    def test_calculate_tb_label(self):
        '''Convert terabyte labels to x * 10^12 bytes.'''
        size_str = '15tb'
        drive_size = 20 * 1000 * 1000 * 1000 * 1000
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(
            size_str=size_str, context=drive)

        assert calc_size == 15 * 1000 * 1000 * 1000 * 1000

    def test_calculate_T_label(self):
        '''Convert terabyte labels to x * 10^12 bytes.'''
        size_str = '15T'
        drive_size = 20 * 1000 * 1000 * 1000 * 1000
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(
            size_str=size_str, context=drive)

        assert calc_size == 15 * 1000 * 1000 * 1000 * 1000

    def test_calculate_TB_label(self):
        '''Convert terabyte labels to x * 10^12 bytes.'''
        size_str = '15TB'
        drive_size = 20 * 1000 * 1000 * 1000 * 1000
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(
            size_str=size_str, context=drive)

        assert calc_size == 15 * 1000 * 1000 * 1000 * 1000

    def test_calculate_percent_blockdev(self):
        '''Convert a percent of total blockdev space to explicit byte count.'''
        drive_size = 20 * 1000 * 1000  # 20 mb drive
        part_size = math.floor(.2 * drive_size)  # calculate 20% of drive size
        size_str = '20%'

        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(
            size_str=size_str, context=drive)

        assert calc_size == part_size

    def test_calculate_percent_vg(self):
        '''Convert a percent of total blockdev space to explicit byte count.'''
        vg_size = 20 * 1000 * 1000  # 20 mb drive
        lv_size = math.floor(.2 * vg_size)  # calculate 20% of drive size
        size_str = '20%'

        vg = VolumeGroup(None, size=vg_size, available_size=vg_size)

        calc_size = ApplyNodeStorage.calculate_bytes(
            size_str=size_str, context=vg)

        assert calc_size == lv_size

    def test_calculate_overprovision(self):
        '''When calculated space is higher than available space, raise an exception.'''
        vg_size = 20 * 1000 * 1000  # 20 mb drive
        vg_available = 10  # 10 bytes available
        size_str = '80%'

        vg = VolumeGroup(None, size=vg_size, available_size=vg_available)

        with pytest.raises(error.NotEnoughStorage):
            ApplyNodeStorage.calculate_bytes(size_str=size_str, context=vg)

    def test_calculate_min_label(self):
        '''Adding the min marker '>' should provision all available space.'''
        vg_size = 20 * 1000 * 1000  # 20 mb drive
        vg_available = 15 * 1000 * 1000
        size_str = '>10%'

        vg = VolumeGroup(None, size=vg_size, available_size=vg_available)

        calc_size = ApplyNodeStorage.calculate_bytes(
            size_str=size_str, context=vg)

        assert calc_size == vg_available - ApplyNodeStorage.PART_TABLE_RESERVATION

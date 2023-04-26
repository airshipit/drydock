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
        drive_size = 20 * 10**6
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(size_str=size_str,
                                                     context=drive)

        assert calc_size == 15 * 10**6

    def test_calculate_mb_label(self):
        '''Convert megabyte labels to x * 10^6 bytes.'''
        size_str = '15mb'
        drive_size = 20 * 10**6
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(size_str=size_str,
                                                     context=drive)

        assert calc_size == 15 * 10**6

    def test_calculate_M_label(self):
        '''Convert megabyte labels to x * 10^6 bytes.'''
        size_str = '15M'
        drive_size = 20 * 10**6
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(size_str=size_str,
                                                     context=drive)

        assert calc_size == 15 * 10**6

    def test_calculate_MB_label(self):
        '''Convert megabyte labels to x * 10^6 bytes.'''
        size_str = '15MB'
        drive_size = 20 * 10**6
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(size_str=size_str,
                                                     context=drive)

        assert calc_size == 15 * 10**6

    def test_calculate_g_label(self):
        '''Convert gigabyte labels to x * 10^9 bytes.'''
        size_str = '15g'
        drive_size = 20 * 10**9
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(size_str=size_str,
                                                     context=drive)

        assert calc_size == 15 * 10**9

    def test_calculate_gb_label(self):
        '''Convert gigabyte labels to x * 10^9 bytes.'''
        size_str = '15gb'
        drive_size = 20 * 10**9
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(size_str=size_str,
                                                     context=drive)

        assert calc_size == 15 * 10**9

    def test_calculate_G_label(self):
        '''Convert gigabyte labels to x * 10^9 bytes.'''
        size_str = '15G'
        drive_size = 20 * 10**9
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(size_str=size_str,
                                                     context=drive)

        assert calc_size == 15 * 10**9

    def test_calculate_GB_label(self):
        '''Convert gigabyte labels to x * 10^9 bytes.'''
        size_str = '15GB'
        drive_size = 20 * 10**9
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(size_str=size_str,
                                                     context=drive)

        assert calc_size == 15 * 10**9

    def test_calculate_t_label(self):
        '''Convert terabyte labels to x * 10^12 bytes.'''
        size_str = '15t'
        drive_size = 20 * 10**12
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(size_str=size_str,
                                                     context=drive)

        assert calc_size == 15 * 10**12

    def test_calculate_tb_label(self):
        '''Convert terabyte labels to x * 10^12 bytes.'''
        size_str = '15tb'
        drive_size = 20 * 10**12
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(size_str=size_str,
                                                     context=drive)

        assert calc_size == 15 * 10**12

    def test_calculate_T_label(self):
        '''Convert terabyte labels to x * 10^12 bytes.'''
        size_str = '15T'
        drive_size = 20 * 10**12
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(size_str=size_str,
                                                     context=drive)

        assert calc_size == 15 * 10**12

    def test_calculate_TB_label(self):
        '''Convert terabyte labels to x * 10^12 bytes.'''
        size_str = '15TB'
        drive_size = 20 * 10**12
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(size_str=size_str,
                                                     context=drive)

        assert calc_size == 15 * 10**12

    def test_calculate_mi_label(self):
        '''Convert mebibyte labels to x * 2^20 bytes.'''
        size_str = '15mi'
        drive_size = 20 * 2**20
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(size_str=size_str,
                                                     context=drive)

        assert calc_size == 15 * 2**20

    def test_calculate_mib_label(self):
        '''Convert mebibyte labels to x * 2^20 bytes.'''
        size_str = '15mib'
        drive_size = 20 * 2**20
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(size_str=size_str,
                                                     context=drive)

        assert calc_size == 15 * 2**20

    def test_calculate_Mi_label(self):
        '''Convert mebibyte labels to x * 2^20 bytes.'''
        size_str = '15Mi'
        drive_size = 20 * 2**20
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(size_str=size_str,
                                                     context=drive)

        assert calc_size == 15 * 2**20

    def test_calculate_MiB_label(self):
        '''Convert mebibyte labels to x * 2^20 bytes.'''
        size_str = '15MiB'
        drive_size = 20 * 2**20
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(size_str=size_str,
                                                     context=drive)

        assert calc_size == 15 * 2**20

    def test_calculate_gi_label(self):
        '''Convert gibibyte labels to x * 2^30 bytes.'''
        size_str = '15gi'
        drive_size = 20 * 2**30
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(size_str=size_str,
                                                     context=drive)

        assert calc_size == 15 * 2**30

    def test_calculate_gib_label(self):
        '''Convert gibibyte labels to x * 2^30 bytes.'''
        size_str = '15gib'
        drive_size = 20 * 2**30
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(size_str=size_str,
                                                     context=drive)

        assert calc_size == 15 * 2**30

    def test_calculate_Gi_label(self):
        '''Convert gibibyte labels to x * 2^30 bytes.'''
        size_str = '15Gi'
        drive_size = 20 * 2**30
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(size_str=size_str,
                                                     context=drive)

        assert calc_size == 15 * 2**30

    def test_calculate_GiB_label(self):
        '''Convert gibibyte labels to x * 2^30 bytes.'''
        size_str = '15GiB'
        drive_size = 20 * 2**30
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(size_str=size_str,
                                                     context=drive)

        assert calc_size == 15 * 2**30

    def test_calculate_ti_label(self):
        '''Convert tebibyte labels to x * 2^40 bytes.'''
        size_str = '15ti'
        drive_size = 20 * 2**40
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(size_str=size_str,
                                                     context=drive)

        assert calc_size == 15 * 2**40

    def test_calculate_tib_label(self):
        '''Convert tebibyte labels to x * 2^40 bytes.'''
        size_str = '15tib'
        drive_size = 20 * 2**40
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(size_str=size_str,
                                                     context=drive)

        assert calc_size == 15 * 2**40

    def test_calculate_Ti_label(self):
        '''Convert tebibyte labels to x * 2^40 bytes.'''
        size_str = '15Ti'
        drive_size = 20 * 2**40
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(size_str=size_str,
                                                     context=drive)

        assert calc_size == 15 * 2**40

    def test_calculate_TiB_label(self):
        '''Convert tebibyte labels to x * 2^40 bytes.'''
        size_str = '15TiB'
        drive_size = 20 * 2**40
        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(size_str=size_str,
                                                     context=drive)

        assert calc_size == 15 * 2**40

    def test_calculate_percent_blockdev(self):
        '''Convert a percent of total blockdev space to explicit byte count.'''
        drive_size = 20 * 10**6  # 20 mb drive
        part_size = math.floor(.2 * drive_size)  # calculate 20% of drive size
        size_str = '20%'

        drive = BlockDevice(None, size=drive_size, available_size=drive_size)

        calc_size = ApplyNodeStorage.calculate_bytes(size_str=size_str,
                                                     context=drive)

        assert calc_size == part_size

    def test_calculate_percent_vg(self):
        '''Convert a percent of total blockdev space to explicit byte count.'''
        vg_size = 20 * 10**6  # 20 mb drive
        lv_size = math.floor(.2 * vg_size)  # calculate 20% of drive size
        size_str = '20%'

        vg = VolumeGroup(None, size=vg_size, available_size=vg_size)

        calc_size = ApplyNodeStorage.calculate_bytes(size_str=size_str,
                                                     context=vg)

        assert calc_size == lv_size

    def test_calculate_overprovision(self):
        '''When calculated space is higher than available space, raise an exception.'''
        vg_size = 20 * 10**6  # 20 mb drive
        vg_available = 10  # 10 bytes available
        size_str = '80%'

        vg = VolumeGroup(None, size=vg_size, available_size=vg_available)

        with pytest.raises(error.NotEnoughStorage):
            ApplyNodeStorage.calculate_bytes(size_str=size_str, context=vg)

    def test_calculate_min_label(self):
        '''Adding the min marker '>' should provision all available space.'''
        vg_size = 20 * 10**6  # 20 mb drive
        vg_available = 15 * 10**6
        size_str = '>10%'

        vg = VolumeGroup(None, size=vg_size, available_size=vg_available)

        calc_size = ApplyNodeStorage.calculate_bytes(size_str=size_str,
                                                     context=vg)

        assert calc_size == vg_available - ApplyNodeStorage.PART_TABLE_RESERVATION

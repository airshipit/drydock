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
"""Utility Classes For Ochestrator"""

import re
import drydock_provisioner.error as errors


class SimpleBytes():
    def calulate_bytes(size_str):
        """
        Calculate the size in bytes of a size_str.

        #m or #M or #mb or #MB = # * 1024 * 1024
        #g or #G or #gb or #GB = # * 1024 * 1024 * 1024
        #t or #T or #tb or #TB = # * 1024 * 1024 * 1024 * 1024

        :param size_str: A string representing the desired size
        :return size: The calculated size in bytes
        """
        pattern = '(\d+)([mMbBgGtT]{1,2})'
        regex = re.compile(pattern)
        match = regex.match(size_str)

        if not match:
            raise errors.InvalidSizeFormat(
                "Invalid size string format: %s" % size_str)

        base_size = int(match.group(1))

        if match.group(2) in ['m', 'M', 'mb', 'MB']:
            computed_size = base_size * (1000 * 1000)
        elif match.group(2) in ['g', 'G', 'gb', 'GB']:
            computed_size = base_size * (1000 * 1000 * 1000)
        elif match.group(2) in ['t', 'T', 'tb', 'TB']:
            computed_size = base_size * (1000 * 1000 * 1000 * 1000)

        return computed_size

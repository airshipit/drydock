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
"""Test that rack models are properly parsed."""
import base64

import drydock_provisioner.objects as objects


class TestClass(object):

    def test_bootaction_pipeline_base64(self):
        objects.register_all()

        ba = objects.BootActionAsset()

        orig = 'Test 1 2 3!'.encode('utf-8')
        expected_value = base64.b64encode(orig)

        test_value = ba.execute_pipeline(orig, ['base64_encode'])

        assert expected_value == test_value

    def test_bootaction_pipeline_utf8(self):
        objects.register_all()

        ba = objects.BootActionAsset()

        expected_value = 'Test 1 2 3!'
        orig = expected_value.encode('utf-8')

        test_value = ba.execute_pipeline(orig, ['utf8_decode'])

        assert test_value == expected_value

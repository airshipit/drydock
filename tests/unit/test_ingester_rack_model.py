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

from drydock_provisioner.statemgmt.state import DrydockState
import drydock_provisioner.objects as objects
import drydock_provisioner.error as errors

import pytest


class TestClass(object):
    def test_rack_parse(self, deckhand_ingester, input_files, setup):
        objects.register_all()

        input_file = input_files.join("deckhand_fullsite.yaml")

        design_state = DrydockState()
        design_ref = "file://%s" % str(input_file)

        design_status, design_data = deckhand_ingester.ingest_data(
            design_state=design_state, design_ref=design_ref)

        print("%s" % str(design_status.to_dict()))
        assert design_status.status == objects.fields.ValidationResult.Success
        rack = design_data.get_rack('rack1')

        assert rack.location.get('grid') == 'EG12'

    def test_rack_not_found(self, deckhand_ingester, input_files, setup):
        objects.register_all()

        input_file = input_files.join("deckhand_fullsite.yaml")

        design_state = DrydockState()
        design_ref = "file://%s" % str(input_file)

        design_status, design_data = deckhand_ingester.ingest_data(
            design_state=design_state, design_ref=design_ref)

        with pytest.raises(errors.DesignError):
            design_data.get_rack('foo')

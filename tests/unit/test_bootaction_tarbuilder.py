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

import ulid2
import tarfile
import io

import drydock_provisioner.objects as objects
from drydock_provisioner.statemgmt.state import DrydockState
from drydock_provisioner.control.bootaction import BootactionUtils


class TestClass(object):
    def test_bootaction_tarbuilder(self, input_files, deckhand_ingester,
                                   setup):
        objects.register_all()

        input_file = input_files.join("deckhand_fullsite.yaml")

        design_state = DrydockState()
        design_ref = "file://%s" % str(input_file)

        design_status, design_data = deckhand_ingester.ingest_data(
            design_state=design_state, design_ref=design_ref)

        target_host = 'compute01'

        ba = design_data.get_bootaction('helloworld')
        action_id = ulid2.generate_binary_ulid()
        assets = ba.render_assets(target_host, design_data, action_id)

        assert len(assets) > 0

        tarbytes = BootactionUtils.tarbuilder(assets)

        assert tarbytes is not None

        fileobj = io.BytesIO(tarbytes)
        tarball = tarfile.open(mode='r:gz', fileobj=fileobj)

        tarasset = tarball.getmember('/var/tmp/hello.sh')

        assert tarasset.mode == 0o555

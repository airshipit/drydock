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
"""Test Versions API"""

from drydock_provisioner.control.api import VersionsResource

import falcon


def test_get_versions(mocker):
    api = VersionsResource()

    # Configure mocked request and response
    req = mocker.MagicMock(spec=falcon.Request)
    resp = mocker.MagicMock(spec=falcon.Response)

    api.on_get(req, resp)

    expected = api.to_json({'v1.0': {'path': '/api/v1.0', 'status': 'stable'}})

    assert resp.text == expected
    assert resp.status == falcon.HTTP_200

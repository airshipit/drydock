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

import drydock_provisioner.drydock_client.session as dc_session
import drydock_provisioner.drydock_client.client as dc_client

def test_blank_session_error():
    with pytest.raises(Exception):
        dd_ses = dc_session.DrydockSession()

def test_session_init_minimal():
    port = 9000
    host = 'foo.bar.baz'

    dd_ses = dc_session.DrydockSession(host, port=port)

    assert dd_ses.base_url == "http://%s:%d/api/" % (host, port)

def test_session_init_minimal_no_port():
    host = 'foo.bar.baz'

    dd_ses = dc_session.DrydockSession(host)

    assert dd_ses.base_url == "http://%s/api/" % (host)

def test_session_init_uuid_token():
    host = 'foo.bar.baz'
    token = '5f1e08b6-38ec-4a99-9d0f-00d29c4e325b'

    dd_ses = dc_session.DrydockSession(host, token=token)

    assert dd_ses.base_url == "http://%s/api/" % (host)
    assert dd_ses.token == token

def test_session_init_fernet_token():
    host = 'foo.bar.baz'
    token = 'gAAAAABU7roWGiCuOvgFcckec-0ytpGnMZDBLG9hA7Hr9qfvdZDHjsak39YN98HXxoYLIqVm19Egku5YR3wyI7heVrOmPNEtmr-fIM1rtahudEdEAPM4HCiMrBmiA1Lw6SU8jc2rPLC7FK7nBCia_BGhG17NVHuQu0S7waA306jyKNhHwUnpsBQ'

    dd_ses = dc_session.DrydockSession(host, token=token)
    
    assert dd_ses.base_url == "http://%s/api/" % (host)
    assert dd_ses.token == token

def test_session_init_marker():
    host = 'foo.bar.baz'
    marker = '5f1e08b6-38ec-4a99-9d0f-00d29c4e325b'

    dd_ses = dc_session.DrydockSession(host, marker=marker)

    assert dd_ses.base_url == "http://%s/api/" % (host)
    assert dd_ses.marker == marker


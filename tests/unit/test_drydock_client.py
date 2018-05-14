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
import mock
import responses

import drydock_provisioner.drydock_client.session as dc_session
import drydock_provisioner.drydock_client.client as dc_client


def test_blank_session_error():
    with pytest.raises(Exception):
        dc_session.DrydockSession()


def test_session_init_minimal():
    port = 9000
    host = 'foo.bar.baz'

    dd_ses = dc_session.DrydockSession(host, port=port)

    assert dd_ses.base_url == "http://%s:%d/api/" % (host, port)


def test_session_init_minimal_no_port():
    host = 'foo.bar.baz'

    dd_ses = dc_session.DrydockSession(host)

    assert dd_ses.base_url == "http://%s/api/" % (host)


@responses.activate
def test_session_get():
    responses.add(
        responses.GET,
        'http://foo.bar.baz/api/v1.0/test',
        body='okay',
        status=200)
    host = 'foo.bar.baz'
    token = '5f1e08b6-38ec-4a99-9d0f-00d29c4e325b'
    marker = '40c3eaf6-6a8a-11e7-a4bd-080027ef795a'

    def auth_gen():
        return [('X-Auth-Token', token)]

    dd_ses = dc_session.DrydockSession(host, auth_gen=auth_gen, marker=marker)

    resp = dd_ses.get('v1.0/test')
    req = resp.request

    assert req.headers.get('X-Auth-Token', None) == token
    assert req.headers.get('X-Context-Marker', None) == marker


@responses.activate
@mock.patch.object(
    dc_session.KeystoneClient,
    'get_token',
    return_value='5f1e08b6-38ec-4a99-9d0f-00d29c4e325b')
def test_session_get_returns_401(*args):
    responses.add(
        responses.GET,
        'http://foo.bar.baz/api/v1.0/test',
        body='okay',
        status=401)
    host = 'foo.bar.baz'
    token = '5f1e08b6-38ec-4a99-9d0f-00d29c4e325b'
    marker = '40c3eaf6-6a8a-11e7-a4bd-080027ef795a'

    def auth_gen():
        return [('X-Auth-Token', dc_session.KeystoneClient.get_token())]

    dd_ses = dc_session.DrydockSession(host, auth_gen=auth_gen, marker=marker)

    resp = dd_ses.get('v1.0/test')
    req = resp.request

    assert req.headers.get('X-Auth-Token', None) == token
    assert req.headers.get('X-Context-Marker', None) == marker
    assert dc_session.KeystoneClient.get_token.call_count == 2


@responses.activate
def test_client_task_get():
    task = {
        'action': 'deploy_node',
        'result': 'success',
        'parent_task': '444a1a40-7b5b-4b80-8265-cadbb783fa82',
        'subtasks': [],
        'status': 'complete',
        'result_detail': {
            'detail': ['Node cab23-r720-17 deployed']
        },
        'site_name': 'mec_demo',
        'task_id': '1476902c-758b-49c0-b618-79ff3fd15166',
        'node_list': ['cab23-r720-17'],
        'design_id': 'fcf37ba1-4cde-48e5-a713-57439fc6e526'
    }

    host = 'foo.bar.baz'

    responses.add(
        responses.GET,
        "http://%s/api/v1.0/tasks/1476902c-758b-49c0-b618-79ff3fd15166" %
        (host),
        json=task,
        status=200)

    dd_ses = dc_session.DrydockSession(host)
    dd_client = dc_client.DrydockClient(dd_ses)

    task_resp = dd_client.get_task('1476902c-758b-49c0-b618-79ff3fd15166')

    assert task_resp['status'] == task['status']

@responses.activate
def test_client_get_nodes_for_filter_post():
    node_list = ['node1', 'node2']

    host = 'foo.bar.baz'

    responses.add(
        responses.POST,
        "http://%s/api/v1.0/nodefilter" %
        (host),
        json=node_list,
        status=200)

    dd_ses = dc_session.DrydockSession(host)
    dd_client = dc_client.DrydockClient(dd_ses)

    design_ref = {
        'ref': 'hello'
    }
    validation_resp = dd_client.get_nodes_for_filter(design_ref)

    assert 'node1' in validation_resp
    assert 'node2' in validation_resp

@responses.activate
def test_client_validate_design_post():
    validation = {
        'status': 'success'
    }

    host = 'foo.bar.baz'

    responses.add(
        responses.POST,
        "http://%s/api/v1.0/validatedesign" %
        (host),
        json=validation,
        status=200)

    dd_ses = dc_session.DrydockSession(host)
    dd_client = dc_client.DrydockClient(dd_ses)

    validation_resp = dd_client.validate_design('href-placeholder')

    assert validation_resp['status'] == validation['status']

# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
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
from unittest import mock
from urllib.parse import urlparse

import pytest
import responses

import drydock_provisioner.error as errors
from drydock_provisioner.drivers.kubernetes.promenade_driver.promenade_client \
    import PromenadeSession, PromenadeClient

PROM_URL = urlparse('http://promhost:80/api/v1.0')
PROM_HOST = 'promhost'


@mock.patch(
    'drydock_provisioner.drivers.kubernetes'
    '.promenade_driver.promenade_client'
    '.PromenadeSession._get_prom_url',
    return_value=PROM_URL)
@mock.patch(
    'drydock_provisioner.drivers.kubernetes'
    '.promenade_driver.promenade_client'
    '.PromenadeSession.set_auth',
    return_value=None)
@responses.activate
def test_put(patch1, patch2):
    """
    Test put functionality
    """
    responses.add(
        responses.PUT,
        'http://promhost:80/api/v1.0/node-label/n1',
        body='{"key1":"label1"}',
        status=200)

    prom_session = PromenadeSession()
    result = prom_session.put('v1.0/node-label/n1',
                              body='{"key1":"label1"}',
                              timeout=(60, 60))

    assert PROM_HOST == prom_session.host
    assert result.status_code == 200


@mock.patch(
    'drydock_provisioner.drivers.kubernetes'
    '.promenade_driver.promenade_client'
    '.PromenadeSession._get_prom_url',
    return_value=PROM_URL)
@mock.patch(
    'drydock_provisioner.drivers.kubernetes'
    '.promenade_driver.promenade_client'
    '.PromenadeSession.set_auth',
    return_value=None)
@responses.activate
def test_get(patch1, patch2):
    """
    Test get functionality
    """
    responses.add(
        responses.GET,
        'http://promhost:80/api/v1.0/node-label/n1',
        status=200)

    prom_session = PromenadeSession()
    result = prom_session.get('v1.0/node-label/n1',
                              timeout=(60, 60))

    assert result.status_code == 200


@mock.patch(
    'drydock_provisioner.drivers.kubernetes'
    '.promenade_driver.promenade_client'
    '.PromenadeSession._get_prom_url',
    return_value=PROM_URL)
@mock.patch(
    'drydock_provisioner.drivers.kubernetes'
    '.promenade_driver.promenade_client'
    '.PromenadeSession.set_auth',
    return_value=None)
@responses.activate
def test_post(patch1, patch2):
    """
    Test post functionality
    """
    responses.add(
        responses.POST,
        'http://promhost:80/api/v1.0/node-label/n1',
        body='{"key1":"label1"}',
        status=200)

    prom_session = PromenadeSession()
    result = prom_session.post('v1.0/node-label/n1',
                               body='{"key1":"label1"}',
                               timeout=(60, 60))

    assert PROM_HOST == prom_session.host
    assert result.status_code == 200


@mock.patch(
    'drydock_provisioner.drivers.kubernetes'
    '.promenade_driver.promenade_client'
    '.PromenadeSession._get_prom_url',
    return_value=PROM_URL)
@mock.patch(
    'drydock_provisioner.drivers.kubernetes'
    '.promenade_driver.promenade_client'
    '.PromenadeSession.set_auth',
    return_value=None)
@responses.activate
def test_relabel_node(patch1, patch2):
    """
    Test relabel node call from Promenade
    Client
    """
    responses.add(
        responses.PUT,
        'http://promhost:80/api/v1.0/node-labels/n1',
        body='{"key1":"label1"}',
        status=200)

    prom_client = PromenadeClient()

    result = prom_client.relabel_node('n1', {"key1": "label1"})

    assert result == {"key1": "label1"}


@mock.patch(
    'drydock_provisioner.drivers.kubernetes'
    '.promenade_driver.promenade_client'
    '.PromenadeSession._get_prom_url',
    return_value=PROM_URL)
@mock.patch(
    'drydock_provisioner.drivers.kubernetes'
    '.promenade_driver.promenade_client'
    '.PromenadeSession.set_auth',
    return_value=None)
@responses.activate
def test_relabel_node_403_status(patch1, patch2):
    """
    Test relabel node with 403 resp status
    """
    responses.add(
        responses.PUT,
        'http://promhost:80/api/v1.0/node-labels/n1',
        body='{"key1":"label1"}',
        status=403)

    prom_client = PromenadeClient()

    with pytest.raises(errors.ClientForbiddenError):
        prom_client.relabel_node('n1', {"key1": "label1"})

@mock.patch(
    'drydock_provisioner.drivers.kubernetes'
    '.promenade_driver.promenade_client'
    '.PromenadeSession._get_prom_url',
    return_value=PROM_URL)
@mock.patch(
    'drydock_provisioner.drivers.kubernetes'
    '.promenade_driver.promenade_client'
    '.PromenadeSession.set_auth',
    return_value=None)
@responses.activate
def test_relabel_node_401_status(patch1, patch2):
    """
    Test relabel node with 401 resp status
    """
    responses.add(
        responses.PUT,
        'http://promhost:80/api/v1.0/node-labels/n1',
        body='{"key1":"label1"}',
        status=401)

    prom_client = PromenadeClient()

    with pytest.raises(errors.ClientUnauthorizedError):
        prom_client.relabel_node('n1', {"key1": "label1"})

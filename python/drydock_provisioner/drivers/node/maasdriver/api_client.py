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
"""Client for submitting authenticated requests to MaaS API."""

import logging

from oauthlib import oauth1
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import requests.auth as req_auth
import base64

import drydock_provisioner.error as errors


class MaasOauth(req_auth.AuthBase):

    def __init__(self, apikey):
        self.consumer_key, self.token_key, self.token_secret = apikey.split(
            ':')
        self.consumer_secret = ""
        self.realm = "OAuth"

        self.oauth_client = oauth1.Client(
            self.consumer_key,
            self.consumer_secret,
            self.token_key,
            self.token_secret,
            signature_method=oauth1.SIGNATURE_PLAINTEXT,
            realm=self.realm)

    def __call__(self, req):
        headers = req.headers
        url = req.url
        method = req.method
        body = None if req.body is None or len(req.body) == 0 else req.body

        new_url, signed_headers, new_body = self.oauth_client.sign(
            url, method, body, headers)

        req.headers['Authorization'] = signed_headers['Authorization']

        return req


class MaasRequestFactory(object):

    def __init__(self, base_url, apikey):
        # The URL in the config should end in /MAAS/, but the api is behind /MAAS/api/2.0/
        self.base_url = base_url + "/api/2.0/"
        self.apikey = apikey

        # Adapter for maas for request retries
        retry_strategy = Retry(total=3,
                               status_forcelist=[429, 500, 502, 503, 504],
                               allowed_methods=[
                                   "HEAD", "GET", "POST", "PUT", "DELETE",
                                   "OPTIONS", "TRACE"
                               ])
        self.maas_adapter = HTTPAdapter(max_retries=retry_strategy)

        self.signer = MaasOauth(apikey)
        self.http_session = requests.Session()
        self.http_session.mount(self.base_url, self.maas_adapter)

        # TODO(sh8121att) Get logger name from config
        self.logger = logging.getLogger('drydock')

    def get(self, endpoint, **kwargs):
        return self._send_request('GET', endpoint, **kwargs)

    def post(self, endpoint, **kwargs):
        return self._send_request('POST', endpoint, **kwargs)

    def delete(self, endpoint, **kwargs):
        return self._send_request('DELETE', endpoint, **kwargs)

    def put(self, endpoint, **kwargs):
        return self._send_request('PUT', endpoint, **kwargs)

    def test_connectivity(self):
        try:
            resp = self.get('version/')
        except requests.Timeout:
            raise errors.TransientDriverError("Timeout connection to MaaS")

        if resp.status_code in [500, 503]:
            raise errors.TransientDriverError("Received 50x error from MaaS")

        if resp.status_code != 200:
            raise errors.PersistentDriverError(
                "Received unexpected error from MaaS")

        return True

    def test_authentication(self):
        try:
            resp = self.get('account/', op='list_authorisation_tokens')
        except requests.Timeout:
            raise errors.TransientDriverError("Timeout connection to MaaS")
        except Exception as ex:
            raise errors.PersistentDriverError("Error accessing MaaS: %s" %
                                               str(ex))

        if resp.status_code in [401, 403]:
            raise errors.PersistentDriverError(
                "MaaS API Authentication Failed")

        if resp.status_code in [500, 503]:
            raise errors.TransientDriverError("Received 50x error from MaaS")

        if resp.status_code != 200:
            raise errors.PersistentDriverError(
                "Received unexpected error from MaaS")

        return True

    def _send_request(self, method, endpoint, **kwargs):
        # Delete auth mechanism if defined
        kwargs.pop('auth', None)

        headers = kwargs.pop('headers', {})

        if 'Accept' not in headers.keys():
            headers['Accept'] = 'application/json'

        if kwargs.get('files', None) is not None:
            files = kwargs.pop('files')

            files_tuples = []

            for (k, v) in files.items():
                if v is None:
                    v = ""

                if isinstance(v, list):
                    for i in v:
                        value = base64.b64encode(
                            str(i).encode('utf-8')).decode('utf-8')
                        content_type = 'text/plain; charset="utf-8"'
                        part_headers = {'Content-Transfer-Encoding': 'base64'}
                        files_tuples.append(
                            (k, (None, value, content_type, part_headers)))
                else:
                    value = base64.b64encode(
                        str(v).encode('utf-8')).decode('utf-8')
                    content_type = 'text/plain; charset="utf-8"'
                    part_headers = {'Content-Transfer-Encoding': 'base64'}
                    files_tuples.append(
                        (k, (None, value, content_type, part_headers)))
            kwargs['files'] = files_tuples

        params = kwargs.pop('params', None)

        if params is None and 'op' in kwargs.keys():
            params = {'op': kwargs.pop('op')}
        elif 'op' in kwargs.keys() and 'op' not in params.keys():
            params['op'] = kwargs.pop('op')
        elif 'op' in kwargs.keys():
            kwargs.pop('op')

        # TODO(sh8121att) timeouts should be configurable
        timeout = kwargs.pop('timeout', None)
        if timeout is None:
            timeout = (5, 60)

        request = requests.Request(method=method,
                                   url=self.base_url + endpoint,
                                   auth=self.signer,
                                   headers=headers,
                                   params=params,
                                   **kwargs)

        prepared_req = self.http_session.prepare_request(request)

        resp = self.http_session.send(prepared_req, timeout=timeout)

        if resp.status_code >= 400:
            self.logger.debug(
                "Received error response - URL: %s %s - RESPONSE: %s" %
                (prepared_req.method, prepared_req.url, resp.status_code))
            self.logger.debug("Response content: %s" % resp.text)
            raise errors.DriverError("MAAS Error: %s - %s" %
                                     (resp.status_code, resp.text))
        return resp

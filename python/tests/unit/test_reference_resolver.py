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
"""Test the data reference resolver."""

import base64

import responses

from drydock_provisioner.statemgmt.design.resolver import ReferenceResolver


class TestClass(object):

    def test_resolve_file_url(self, input_files):
        """Test that the resolver will resolve file URLs."""
        input_file = input_files.join("fullsite.yaml")
        url = 'file://%s' % str(input_file)

        content = ReferenceResolver.resolve_reference(url)

        assert len(content) > 0

    @responses.activate
    def test_resolve_http_url(self):
        """Test that the resolver will resolve http URLs."""
        url = 'http://foo.com/test.yaml'
        responses.add(responses.GET, url)

        ReferenceResolver.resolve_reference(url)

        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == url

    @responses.activate
    def test_resolve_http_basicauth_url(self):
        """Test the resolver will resolve http URLs w/ basic auth."""
        url = 'http://user:pass@foo.com/test.yaml'
        auth_header = "Basic %s" % base64.b64encode(
            "user:pass".encode('utf-8')).decode('utf-8')
        responses.add(responses.GET, url)

        ReferenceResolver.resolve_reference(url)

        assert len(responses.calls) == 1
        assert 'Authorization' in responses.calls[0].request.headers
        assert responses.calls[0].request.headers.get(
            'Authorization') == auth_header

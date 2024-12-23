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
import responses

from drydock_provisioner.drydock_client.session import DrydockSession


class TestClientSession(object):

    def test_create_session(self):
        """Tests setting up an Drydock client session"""
        sess = DrydockSession("testdrydock")
        assert sess.default_timeout == (20, 30)

        sess = DrydockSession("testdrydock", timeout=60)
        assert sess.default_timeout == (20, 60)

        sess = DrydockSession("testdrydock", timeout=(300, 300))
        assert sess.default_timeout == (300, 300)

        sess = DrydockSession("testdrydock", timeout=("cheese", "chicken"))
        assert sess.default_timeout == (20, 30)

        sess = DrydockSession("testdrydock", timeout=(30, 60, 90))
        assert sess.default_timeout == (20, 30)

        sess = DrydockSession("testdrydock", timeout="cranium")
        assert sess.default_timeout == (20, 30)

    get_responses_inp = {
        'method': 'GET',
        'url': 'http://testdrydock/api/bogus',
        'body': 'got it',
        'status': 200,
        'content_type': 'text/plain'
    }

    @responses.activate
    def test_get(self):
        """Tests the get method"""
        responses.add(**TestClientSession.get_responses_inp)
        sess = DrydockSession("testdrydock")
        result = sess.get('bogus')
        assert result.status_code == 200

    @responses.activate
    def test_get_with_timeout(self):
        """Tests the get method"""
        responses.add(**TestClientSession.get_responses_inp)
        sess = DrydockSession("testdrydock")
        result = sess.get('bogus', timeout=(60, 60))
        assert result.status_code == 200

    post_responses_inp = {
        'method': 'POST',
        'url': 'http://testdrydock/api/bogus',
        'body': 'got it',
        'status': 200,
        'content_type': 'text/plain'
    }

    @responses.activate
    def test_post(self):
        """Tests the post method"""
        responses.add(**TestClientSession.post_responses_inp)
        sess = DrydockSession("testdrydock")
        result = sess.post('bogus')
        assert result.status_code == 200

    @responses.activate
    def test_post_with_timeout(self):
        """Tests the post method"""
        responses.add(**TestClientSession.post_responses_inp)
        sess = DrydockSession("testdrydock")
        result = sess.post('bogus', timeout=(60, 60))
        assert result.status_code == 200

    def test_timeout(self):
        """Tests the _timeout method"""
        sess = DrydockSession("testdrydock")
        resp = sess._timeout((60, 70))
        assert resp == (60, 70)

        resp = sess._timeout()
        assert resp == (20, 30)

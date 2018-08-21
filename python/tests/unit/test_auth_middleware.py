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
import uuid
import falcon
import sys

from drydock_provisioner.control.base import DrydockRequest
from drydock_provisioner.control.middleware import AuthMiddleware


class TestAuthMiddleware():

    # the WSGI env for a request processed by keystone middleware
    # with user token
    ks_user_env = {
        'REQUEST_METHOD': 'GET',
        'SCRIPT_NAME': '/foo',
        'PATH_INFO': '',
        'QUERY_STRING': '',
        'CONTENT_TYPE': '',
        'CONTENT_LENGTH': 0,
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '9000',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'HTTP_X_IDENTITY_STATUS': 'Confirmed',
        'HTTP_X_PROJECT_ID': '',
        'HTTP_X_USER_ID': '',
        'HTTP_X_AUTH_TOKEN': '',
        'HTTP_X_ROLES': '',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.input': sys.stdin,
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
    }

    # the WSGI env for a request processed by keystone middleware
    # with service token
    ks_service_env = {
        'REQUEST_METHOD': 'GET',
        'SCRIPT_NAME': '/foo',
        'PATH_INFO': '',
        'QUERY_STRING': '',
        'CONTENT_TYPE': '',
        'CONTENT_LENGTH': 0,
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '9000',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'HTTP_X_SERVICE_IDENTITY_STATUS': 'Confirmed',
        'HTTP_X_SERVICE_PROJECT_ID': '',
        'HTTP_X_SERVICE_USER_ID': '',
        'HTTP_X_SERVICE_TOKEN': '',
        'HTTP_X_ROLES': '',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.input': sys.stdin,
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
    }

    def test_process_request_user(self):
        ''' AuthMiddleware is expected to correctly identify the headers
            added to an authenticated request by keystonemiddleware in a
            PasteDeploy configuration
        '''

        req_env = TestAuthMiddleware.ks_user_env

        project_id = str(uuid.uuid4().hex)
        req_env['HTTP_X_PROJECT_ID'] = project_id
        user_id = str(uuid.uuid4().hex)
        req_env['HTTP_X_USER_ID'] = user_id
        token = str(uuid.uuid4().hex)
        req_env['HTTP_X_AUTH_TOKEN'] = token

        middleware = AuthMiddleware()
        request = DrydockRequest(req_env)
        response = falcon.Response()

        middleware.process_request(request, response)

        assert request.context.authenticated
        assert request.context.user_id == user_id

    def test_process_request_user_noauth(self):
        ''' AuthMiddleware is expected to correctly identify the headers
            added to an unauthenticated (no token, bad token) request by
            keystonemiddleware in a PasteDeploy configuration
        '''

        req_env = TestAuthMiddleware.ks_user_env

        req_env['HTTP_X_IDENTITY_STATUS'] = 'Invalid'

        middleware = AuthMiddleware()
        request = DrydockRequest(req_env)
        response = falcon.Response()

        middleware.process_request(request, response)

        assert request.context.authenticated is False

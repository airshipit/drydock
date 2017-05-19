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
import falcon.request as request
import uuid

class BaseResource(object):

    def on_options(self, req, resp):
        self_attrs = dir(self)
        methods = ['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'PATCH']
        allowed_methods = []

        for m in methods:
            if 'on_' + m.lower() in self_attrs:
                allowed_methods.append(m)

        resp.headers['Allow'] = ','.join(allowed_methods)
        resp.status = falcon.HTTP_200

    # By default, no one is authorized to use a resource
    def authorize_roles(self, role_list):
        return False

class StatefulResource(BaseResource):

    def __init__(self, state_manager=None):
        super(StatefulResource, self).__init__()

        if state_manager is None:
            raise ValueError("StatefulResources require a state manager be set")

        self.state_manager = state_manager


class DrydockRequestContext(object):

    def __init__(self):
        self.log_level = 'error'
        self.user = None
        self.roles = ['anyone']
        self.request_id = str(uuid.uuid4())
        self.external_marker = None

    def set_log_level(self, level):
        if level in ['error', 'info', 'debug']:
            self.log_level = level

    def set_user(self, user):
        self.user = user

    def add_role(self, role):
        self.roles.append(role)

    def add_roles(self, roles):
        self.roles.extend(roles)

    def remove_role(self, role):
        self.roles = [x for x in self.roles
                      if x != role]

    def set_external_marker(self, marker):
        self.external_marker = str(marker)[:32]

class DrydockRequest(request.Request)
    context_type = DrydockRequestContext
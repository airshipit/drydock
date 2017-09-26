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
import json
import logging

import falcon
import falcon.request

import drydock_provisioner.error as errors


class BaseResource(object):
    def __init__(self):
        self.logger = logging.getLogger('control')

    def on_options(self, req, resp):
        self_attrs = dir(self)
        methods = ['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'PATCH']
        allowed_methods = []

        for m in methods:
            if 'on_' + m.lower() in self_attrs:
                allowed_methods.append(m)

        resp.headers['Allow'] = ','.join(allowed_methods)
        resp.status = falcon.HTTP_200

    def req_json(self, req):
        if req.content_length is None or req.content_length == 0:
            return None

        if req.content_type is not None and req.content_type.lower(
        ) == 'application/json':
            raw_body = req.stream.read(req.content_length or 0)

            if raw_body is None:
                return None

            try:
                json_body = json.loads(raw_body.decode('utf-8'))
                return json_body
            except json.JSONDecodeError as jex:
                print(
                    "Invalid JSON in request: \n%s" % raw_body.decode('utf-8'))
                self.error(
                    req.context,
                    "Invalid JSON in request: \n%s" % raw_body.decode('utf-8'))
                raise errors.InvalidFormat("%s: Invalid JSON in body: %s" %
                                           (req.path, jex))
        else:
            raise errors.InvalidFormat("Requires application/json payload")

    def return_error(self, resp, status_code, message="", retry=False):
        resp.body = json.dumps({
            'type': 'error',
            'message': message,
            'retry': retry
        })
        resp.status = status_code

    def log_error(self, ctx, level, msg):
        extra = {'user': 'N/A', 'req_id': 'N/A', 'external_ctx': 'N/A'}

        if ctx is not None:
            extra = {
                'user': ctx.user,
                'req_id': ctx.request_id,
                'external_ctx': ctx.external_marker,
            }

        self.logger.log(level, msg, extra=extra)

    def debug(self, ctx, msg):
        self.log_error(ctx, logging.DEBUG, msg)

    def info(self, ctx, msg):
        self.log_error(ctx, logging.INFO, msg)

    def warn(self, ctx, msg):
        self.log_error(ctx, logging.WARN, msg)

    def error(self, ctx, msg):
        self.log_error(ctx, logging.ERROR, msg)


class StatefulResource(BaseResource):
    def __init__(self, state_manager=None, **kwargs):
        super(StatefulResource, self).__init__(**kwargs)

        if state_manager is None:
            self.error(
                None,
                "StatefulResource:init - StatefulResources require a state manager be set"
            )
            raise ValueError(
                "StatefulResources require a state manager be set")

        self.state_manager = state_manager


class DrydockRequestContext(object):
    def __init__(self):
        self.log_level = 'ERROR'
        self.user = None  # Username
        self.user_id = None  # User ID (UUID)
        self.user_domain_id = None  # Domain owning user
        self.roles = []
        self.project_id = None
        self.project_domain_id = None  # Domain owning project
        self.is_admin_project = False
        self.authenticated = False
        self.request_id = str(uuid.uuid4())
        self.external_marker = ''
        self.policy_engine = None

    @classmethod
    def from_dict(cls, d):
        """Instantiate a context from a dictionary of values.

        This is only used to deserialize persisted instances, so we
        will trust the dictionary keys are exactly the correct fields

        :param d: Dictionary of instance values
        """
        i = DrydockRequestContext()

        for k, v in d.items():
            setattr(i, k, v)

        return i

    def to_dict(self):
        return {
            'log_level': self.log_level,
            'user': self.user,
            'user_id': self.user_id,
            'user_domain_id': self.user_domain_id,
            'roles': self.roles,
            'project_id': self.project_id,
            'project_domain_id': self.project_domain_id,
            'is_admin_project': self.is_admin_project,
            'authenticated': self.authenticated,
            'request_id': self.request_id,
            'external_marker': self.external_marker,
        }

    def set_log_level(self, level):
        if level in ['error', 'info', 'debug']:
            self.log_level = level

    def set_user(self, user):
        self.user = user

    def set_project(self, project):
        self.project = project

    def add_role(self, role):
        self.roles.append(role)

    def add_roles(self, roles):
        self.roles.extend(roles)

    def remove_role(self, role):
        self.roles = [x for x in self.roles if x != role]

    def set_external_marker(self, marker):
        self.external_marker = marker

    def set_policy_engine(self, engine):
        self.policy_engine = engine

    def to_policy_view(self):
        policy_dict = {}

        policy_dict['user_id'] = self.user_id
        policy_dict['user_domain_id'] = self.user_domain_id
        policy_dict['project_id'] = self.project_id
        policy_dict['project_domain_id'] = self.project_domain_id
        policy_dict['roles'] = self.roles
        policy_dict['is_admin_project'] = self.is_admin_project

        return policy_dict


class DrydockRequest(falcon.request.Request):
    context_type = DrydockRequestContext

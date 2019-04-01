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
"""Middleware classes for Falcon-based API."""

import logging
import re

from oslo_config import cfg

from drydock_provisioner import policy


class AuthMiddleware(object):
    def __init__(self):
        self.logger = logging.getLogger('drydock')

    # Authentication
    def process_request(self, req, resp):
        ctx = req.context

        ctx.set_policy_engine(policy.policy_engine)

        self.logger.debug(
            "Request with headers: %s" % ','.join(req.headers.keys()))

        auth_status = req.get_header('X-SERVICE-IDENTITY-STATUS')
        service = True

        if auth_status is None:
            auth_status = req.get_header('X-IDENTITY-STATUS')
            service = False

        if auth_status == 'Confirmed':
            # Process account and roles
            ctx.authenticated = True
            ctx.user = req.get_header(
                'X-SERVICE-USER-NAME') if service else req.get_header(
                    'X-USER-NAME')
            ctx.user_id = req.get_header(
                'X-SERVICE-USER-ID') if service else req.get_header(
                    'X-USER-ID')
            ctx.user_domain_id = req.get_header(
                'X-SERVICE-USER-DOMAIN-ID') if service else req.get_header(
                    'X-USER-DOMAIN-ID')
            ctx.project_id = req.get_header(
                'X-SERVICE-PROJECT-ID') if service else req.get_header(
                    'X-PROJECT-ID')
            ctx.project_domain_id = req.get_header(
                'X-SERVICE-PROJECT-DOMAIN-ID') if service else req.get_header(
                    'X-PROJECT-DOMAIN-NAME')
            if service:
                ctx.add_roles(req.get_header('X-SERVICE-ROLES').split(','))
            else:
                ctx.add_roles(req.get_header('X-ROLES').split(','))

            if req.get_header('X-IS-ADMIN-PROJECT') == 'True':
                ctx.is_admin_project = True
            else:
                ctx.is_admin_project = False

            self.logger.debug(
                'Request from authenticated user %s with roles %s' %
                (ctx.user, ','.join(ctx.roles)))
        else:
            self.logger.debug('Request from unauthenticated client.')
            ctx.authenticated = False


class ContextMiddleware(object):
    def __init__(self):
        # Setup validation pattern for external marker
        UUIDv4_pattern = '^[0-9A-F]{8}-[0-9A-F]{4}-4[0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}$'
        self.marker_re = re.compile(UUIDv4_pattern, re.I)

    def process_request(self, req, resp):
        ctx = req.context

        ext_marker = req.get_header('X-Context-Marker')
        end_user = req.get_header('X-End-User')

        if ext_marker is not None and self.marker_re.fullmatch(ext_marker):
            ctx.set_external_marker(ext_marker)

        # Set end user from req header in context obj if available
        # else set the user as end user.
        if end_user is not None:
            ctx.set_end_user(end_user)
        else:
            ctx.set_end_user(ctx.user)


class LoggingMiddleware(object):
    def __init__(self):
        self.logger = logging.getLogger(cfg.CONF.logging.control_logger_name)

    def process_request(self, req, resp):
        extra = {
            'user': req.context.user,
            'req_id': req.context.request_id,
            'external_ctx': req.context.external_marker,
            'end_user': req.context.end_user,
        }
        self.logger.info(
            "Request: %s %s %s" % (req.method, req.uri, req.query_string),
            extra=extra)

    def process_response(self, req, resp, resource, req_succeeded):
        ctx = req.context
        extra = {
            'user': ctx.user,
            'req_id': ctx.request_id,
            'external_ctx': ctx.external_marker,
            'end_user': ctx.end_user,
        }
        resp.append_header('X-Drydock-Req', ctx.request_id)
        self.logger.info(
            "Response: %s %s - %s" % (req.method, req.uri, resp.status),
            extra=extra)

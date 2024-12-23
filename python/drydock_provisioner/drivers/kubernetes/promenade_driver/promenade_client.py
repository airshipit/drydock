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
"""Client for submitting authenticated requests to Promenade API."""

import logging
import requests
from urllib.parse import urlparse

from keystoneauth1 import exceptions as exc

import drydock_provisioner.error as errors
from drydock_provisioner.util import KeystoneUtils


# TODO: Remove this local implementation of Promenade Session and client once
# Promenade api client is available as part of Promenade project.
class PromenadeSession(object):
    """
    A session to the Promenade API maintaining credentials and API options

    :param string marker: (optional) external context marker
    :param tuple timeout: (optional) a tuple of connect, read timeout values
        to use as the default for invocations using this session. A single
        value may also be supplied instead of a tuple to indicate only the
        read timeout to use
    """

    def __init__(self, scheme='http', marker=None, timeout=None):
        self.logger = logging.getLogger(__name__)
        self.__session = requests.Session()

        self.set_auth()

        self.marker = marker
        self.__session.headers.update({'X-Context-Marker': marker})

        self.prom_url = self._get_prom_url()
        self.port = self.prom_url.port
        self.host = self.prom_url.hostname
        self.scheme = scheme

        if self.port:
            self.base_url = "%s://%s:%s/api/" % (self.scheme, self.host,
                                                 self.port)
        else:
            # assume default port for scheme
            self.base_url = "%s://%s/api/" % (self.scheme, self.host)

        self.default_timeout = self._calc_timeout_tuple((20, 30), timeout)

    def set_auth(self):

        auth_header = self._auth_gen()
        self.__session.headers.update(auth_header)

    def get(self, route, query=None, timeout=None):
        """
        Send a GET request to Promenade.

        :param string route: The URL string following the hostname and API prefix
        :param dict query: A dict of k, v pairs to add to the query string
        :param timeout: A single or tuple value for connect, read timeout.
            A single value indicates the read timeout only
        :return: A requests.Response object
        """
        auth_refresh = False
        while True:
            url = self.base_url + route
            self.logger.debug('GET ' + url)
            self.logger.debug('Query Params: ' + str(query))
            resp = self.__session.get(url,
                                      params=query,
                                      timeout=self._timeout(timeout))

            if resp.status_code == 401 and not auth_refresh:
                self.set_auth()
                auth_refresh = True
            else:
                break

        return resp

    def put(self, endpoint, query=None, body=None, data=None, timeout=None):
        """
        Send a PUT request to Promenade. If both body and data are specified,
        body will be used.

        :param string endpoint: The URL string following the hostname and API prefix
        :param dict query: A dict of k, v parameters to add to the query string
        :param string body: A string to use as the request body. Will be treated as raw
        :param data: Something json.dumps(s) can serialize. Result will be used as the request body
        :param timeout: A single or tuple value for connect, read timeout.
            A single value indicates the read timeout only
        :return: A requests.Response object
        """
        auth_refresh = False
        url = self.base_url + endpoint
        while True:
            self.logger.debug('PUT ' + url)
            self.logger.debug('Query Params: ' + str(query))
            if body is not None:
                self.logger.debug("Sending PUT with explicit body: \n%s" %
                                  body)
                resp = self.__session.put(self.base_url + endpoint,
                                          params=query,
                                          data=body,
                                          timeout=self._timeout(timeout))
            else:
                self.logger.debug("Sending PUT with JSON body: \n%s" %
                                  str(data))
                resp = self.__session.put(self.base_url + endpoint,
                                          params=query,
                                          json=data,
                                          timeout=self._timeout(timeout))
            if resp.status_code == 401 and not auth_refresh:
                self.set_auth()
                auth_refresh = True
            else:
                break

        return resp

    def post(self, endpoint, query=None, body=None, data=None, timeout=None):
        """
        Send a POST request to Drydock. If both body and data are specified,
        body will be used.

        :param string endpoint: The URL string following the hostname and API prefix
        :param dict query: A dict of k, v parameters to add to the query string
        :param string body: A string to use as the request body. Will be treated as raw
        :param data: Something json.dumps(s) can serialize. Result will be used as the request body
        :param timeout: A single or tuple value for connect, read timeout.
            A single value indicates the read timeout only
        :return: A requests.Response object
        """
        auth_refresh = False
        url = self.base_url + endpoint
        while True:
            self.logger.debug('POST ' + url)
            self.logger.debug('Query Params: ' + str(query))
            if body is not None:
                self.logger.debug("Sending POST with explicit body: \n%s" %
                                  body)
                resp = self.__session.post(self.base_url + endpoint,
                                           params=query,
                                           data=body,
                                           timeout=self._timeout(timeout))
            else:
                self.logger.debug("Sending POST with JSON body: \n%s" %
                                  str(data))
                resp = self.__session.post(self.base_url + endpoint,
                                           params=query,
                                           json=data,
                                           timeout=self._timeout(timeout))
            if resp.status_code == 401 and not auth_refresh:
                self.set_auth()
                auth_refresh = True
            else:
                break

        return resp

    def _timeout(self, timeout=None):
        """Calculate the default timeouts for this session

        :param timeout: A single or tuple value for connect, read timeout.
            A single value indicates the read timeout only
        :return: the tuple of the default timeouts used for this session
        """
        return self._calc_timeout_tuple(self.default_timeout, timeout)

    def _calc_timeout_tuple(self, def_timeout, timeout=None):
        """Calculate the default timeouts for this session

        :param def_timeout: The default timeout tuple to be used if no specific
            timeout value is supplied
        :param timeout: A single or tuple value for connect, read timeout.
            A single value indicates the read timeout only
        :return: the tuple of the timeouts calculated
        """
        connect_timeout, read_timeout = def_timeout

        try:
            if isinstance(timeout, tuple):
                if all(isinstance(v, int)
                       for v in timeout) and len(timeout) == 2:
                    connect_timeout, read_timeout = timeout
                else:
                    raise ValueError("Tuple non-integer or wrong length")
            elif isinstance(timeout, int):
                read_timeout = timeout
            elif timeout is not None:
                raise ValueError("Non integer timeout value")
        except ValueError:
            self.logger.warning(
                "Timeout value must be a tuple of integers or a "
                "single integer. Proceeding with values of "
                "(%s, %s)", connect_timeout, read_timeout)
        return (connect_timeout, read_timeout)

    def _get_ks_session(self):
        # Get keystone session object

        try:
            ks_session = KeystoneUtils.get_session()
        except exc.AuthorizationFailure as aferr:
            self.logger.error('Could not authorize against Keystone: %s',
                              str(aferr))
            raise errors.DriverError(
                'Could not authorize against Keystone: %s', str(aferr))

        return ks_session

    def _get_prom_url(self):
        # Get promenade url from Keystone session object

        ks_session = self._get_ks_session()

        try:
            prom_endpoint = ks_session.get_endpoint(
                interface='internal', service_type='kubernetesprovisioner')
        except exc.EndpointNotFound:
            self.logger.error("Could not find an internal interface"
                              " defined in Keystone for Promenade")

            raise errors.DriverError("Could not find an internal interface"
                                     " defined in Keystone for Promenade")

        prom_url = urlparse(prom_endpoint)

        return prom_url

    def _auth_gen(self):
        # Get auth token from Keystone session
        token = self._get_ks_session().get_auth_headers().get('X-Auth-Token')
        return [('X-Auth-Token', token)]


class PromenadeClient(object):
    """"
    A client for the Promenade API
    """

    def __init__(self):
        self.session = PromenadeSession()
        self.logger = logging.getLogger(__name__)

    def relabel_node(self, node_id, node_labels):
        """ Relabel kubernetes node

        :param string node_id: Node id for node to be relabeled.
        :param dict node_labels: The dictionary representation of node labels
                                 that needs be re-applied to the node.
        :return: response
        """

        route = 'v1.0/node-labels/{}'.format(node_id)

        self.logger.debug("promenade_client is calling %s API: body is %s" %
                          (route, str(node_labels)))

        resp = self.session.put(route, data=node_labels)

        self._check_response(resp)

        return resp.json()

    def _check_response(self, resp):
        if resp.status_code == 401:
            raise errors.ClientUnauthorizedError(
                "Unauthorized access to %s, include valid token." % resp.url)
        elif resp.status_code == 403:
            raise errors.ClientForbiddenError("Forbidden access to %s" %
                                              resp.url)
        elif not resp.ok:
            raise errors.ClientError("Error - received %d: %s" %
                                     (resp.status_code, resp.text),
                                     code=resp.status_code)

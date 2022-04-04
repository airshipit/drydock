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
import requests
import logging

from keystoneauth1 import session
from keystoneauth1.identity import v3


class DrydockSession(object):
    """
    A session to the Drydock API maintaining credentials and API options

    :param string host: The Drydock server hostname or IP
    :param int port: (optional) The service port appended if specified
    :param function auth_gen: Callable that will generate a list of authentication
                              header names and values (2 part tuple)
    :param string marker: (optional) external context marker
    :param tuple timeout: (optional) a tuple of connect, read timeout values
        to use as the default for invocations using this session. A single
        value may also be supplied instead of a tuple to indicate only the
        read timeout to use
    """

    def __init__(self,
                 host,
                 port=None,
                 scheme='http',
                 auth_gen=None,
                 marker=None,
                 end_user=None,
                 timeout=None):
        self.logger = logging.getLogger(__name__)
        self.__session = requests.Session()
        self.auth_gen = auth_gen

        self.set_auth()

        self.marker = marker
        self.end_user = end_user
        self.__session.headers.update({'X-Context-Marker': marker})

        if end_user:
            self.__session.headers.update({'X-End-User': end_user})

        self.host = host
        self.scheme = scheme

        if port:
            self.port = port
            self.base_url = "%s://%s:%s/api/" % (self.scheme, self.host,
                                                 self.port)
        else:
            # assume default port for scheme
            self.base_url = "%s://%s/api/" % (self.scheme, self.host)

        self.default_timeout = self._calc_timeout_tuple((20, 30), timeout)

    def set_auth(self):
        """Set the session's auth header."""
        if self.auth_gen:
            self.logger.debug("Updating session authentication header.")
            auth_header = self.auth_gen()
            self.__session.headers.update(auth_header)
        else:
            self.logger.debug("Cannot set auth header, no generator defined.")

    def get(self, endpoint, query=None, timeout=None):
        """
        Send a GET request to Drydock.

        :param string endpoint: The URL string following the hostname and API prefix
        :param dict query: A dict of k, v pairs to add to the query string
        :param timeout: A single or tuple value for connect, read timeout.
            A single value indicates the read timeout only
        :return: A requests.Response object
        """
        auth_refresh = False
        while True:
            url = self.base_url + endpoint
            self.logger.debug('GET ' + url)
            self.logger.debug('Query Params: ' + str(query))
            resp = self.__session.get(
                url, params=query, timeout=self._timeout(timeout))

            if resp.status_code == 401 and not auth_refresh:
                self.set_auth()
                auth_refresh = True
            else:
                break

        return resp

    def post(self, endpoint, query=None, body=None, data=None, timeout=None):
        """
        Send a POST request to Drydock. If both body and data are specified,
        body will will be used.

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
                self.logger.debug(
                    "Sending POST with explicit body: \n%s" % body)
                resp = self.__session.post(
                    self.base_url + endpoint,
                    params=query,
                    data=body,
                    timeout=self._timeout(timeout))
            else:
                self.logger.debug(
                    "Sending POST with JSON body: \n%s" % str(data))
                resp = self.__session.post(
                    self.base_url + endpoint,
                    params=query,
                    json=data,
                    timeout=self._timeout(timeout))
            if resp.status_code == 401 and not auth_refresh:
                self.set_auth()
                auth_refresh = True
            else:
                break

        return resp

    def delete(self, endpoint, query=None, timeout=None):
        """
        Send a DELETE request to Drydock. If both body and data are specified,
        body will will be used.

        :param string endpoint: The URL string following the hostname and API prefix
        :param dict query: A dict of k, v pairs to add to the query string
        :param timeout: A single or tuple value for connect, read timeout.
            A single value indicates the read timeout only
        :return: A requests.Response object
        """

        auth_refresh = False
        while True:
            url = self.base_url + endpoint
            self.logger.debug('DELETE ' + url)
            self.logger.debug('Query Params: ' + str(query))
            resp = self.__session.delete(
                url, params=query, timeout=self._timeout(timeout))

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
            self.logger.warn(
                "Timeout value must be a tuple of integers or a "
                "single integer. Proceeding with values of "
                "(%s, %s)", connect_timeout, read_timeout)
        return (connect_timeout, read_timeout)


class KeystoneClient(object):
    @staticmethod
    def get_endpoint(endpoint,
                     ks_sess=None,
                     auth_info=None,
                     interface='internal'):
        """
        Wraps calls to keystone for lookup of an endpoint by service type
        :param endpoint: The endpoint to look up
        :param ks_sess: A keystone session to use for accessing endpoint catalogue
        :param auth_info: Authentication info to use for building a token if a ``ks_sess`` is not specified
        :param str interface: Which registered endpoint to return
        :returns: The url string of the endpoint
        :rtype: str
        """
        if ks_sess is None:
            ks_sess = KeystoneClient.get_ks_session(**auth_info)

        return ks_sess.get_endpoint(interface=interface, service_type=endpoint)

    @staticmethod
    def get_token(ks_sess=None, auth_info=None):
        """
        Returns the simple token string for a token acquired from keystone

        :param ks_sess: an existing Keystone session to retrieve a token from
        :param auth_info: dictionary of information required to generate a keystone token
        """
        if ks_sess is None:
            ks_sess = KeystoneClient.get_ks_session(**auth_info)
        return ks_sess.get_auth_headers().get('X-Auth-Token')

    @staticmethod
    def get_ks_session(**kwargs):
        # Establishes a keystone session
        if 'token' in kwargs:
            auth = v3.TokenMethod(token=kwargs.get('token'))
        else:
            auth = v3.Password(**kwargs)
        return session.Session(auth=auth)

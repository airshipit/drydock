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
"""Module for resolving design references."""

import urllib.parse
import re
import time
import logging

import requests
from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options

from drydock_provisioner import error as errors
from drydock_provisioner.util import KeystoneUtils
from drydock_provisioner.config import config_mgr

cache_opts = {
    'cache.type': 'memory',
    'expire': 180,
}

cache = CacheManager(**parse_cache_config_options(cache_opts))
LOG = logging.getLogger(__name__)


class ReferenceResolver(object):
    """Class for handling different data references to resolve them data."""

    @classmethod
    @cache.cache()
    def resolve_reference(cls, design_ref):
        """Resolve a reference to a design document.

        Locate a schema handler based on the URI scheme of the data reference
        and use that handler to get the data referenced.

        :param design_ref: A URI-formatted reference to a data entity
        """
        try:
            design_uri = urllib.parse.urlparse(design_ref)

            handler = cls.scheme_handlers.get(design_uri.scheme, None)

            if handler is None:
                raise errors.InvalidDesignReference(
                    "Invalid reference scheme %s: no handler." %
                    design_uri.scheme)
            else:
                tries = 0
                while tries < config_mgr.conf.network.http_client_retries:
                    try:
                        # Have to do a little magic to call the classmethod as a pointer
                        return handler.__get__(None, cls)(design_uri)
                    except Exception as ex:
                        tries = tries + 1
                        if tries < config_mgr.conf.network.http_client_retries:
                            LOG.debug("Retrying reference after failure: %s" %
                                      str(ex))
                            time.sleep(5**tries)
        except ValueError:
            raise errors.InvalidDesignReference(
                "Cannot resolve design reference %s: unable to parse as valid URI."
                % design_ref)

    @classmethod
    def resolve_reference_http(cls, design_uri):
        """Retrieve design documents from http/https endpoints.

        Return a byte array of the response content. Support unsecured or
        basic auth

        :param design_uri: Tuple as returned by urllib.parse for the design reference
        """
        if design_uri.username is not None and design_uri.password is not None:
            response = requests.get(design_uri.geturl(),
                                    auth=(design_uri.username,
                                          design_uri.password),
                                    timeout=get_client_timeouts())
        else:
            response = requests.get(design_uri.geturl(),
                                    timeout=get_client_timeouts())

        return response.content

    @classmethod
    def resolve_reference_file(cls, design_uri):
        """Retrieve design documents from local file endpoints.

        Return a byte array of the file contents

        :param design_uri: Tuple as returned by urllib.parse for the design reference
        """
        if design_uri.path != '':
            f = open(design_uri.path, 'rb')
            doc = f.read()
            return doc

    @classmethod
    def resolve_reference_ucp(cls, design_uri):
        """Retrieve artifacts from a Airship service endpoint.

        Return a byte array of the response content. Assumes Keystone
        authentication required.

        :param design_uri: Tuple as returned by urllib.parse for the design reference
        """
        ks_sess = KeystoneUtils.get_session()
        (new_scheme, foo) = re.subn(r'^[^+]+\+', '', design_uri.scheme)
        url = urllib.parse.urlunparse(
            (new_scheme, design_uri.netloc, design_uri.path, design_uri.params,
             design_uri.query, design_uri.fragment))
        LOG.debug("Calling Keystone session for url %s" % str(url))
        resp = ks_sess.get(url, timeout=get_client_timeouts())
        if resp.status_code >= 400:
            raise errors.InvalidDesignReference(
                "Received error code for reference %s: %s - %s" %
                (url, str(resp.status_code), resp.text))
        return resp.content

    scheme_handlers = {
        'http': resolve_reference_http,
        'file': resolve_reference_file,
        'https': resolve_reference_http,
        'deckhand+http': resolve_reference_ucp,
        'promenade+http': resolve_reference_ucp,
    }


def get_client_timeouts():
    """Return a tuple of timeouts for the request library."""
    return (config_mgr.conf.network.http_client_connect_timeout,
            config_mgr.conf.network.http_client_read_timeout)

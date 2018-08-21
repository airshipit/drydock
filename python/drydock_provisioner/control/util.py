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
"""Reusable utility functions for API access."""
from drydock_provisioner.error import ApiError
from drydock_provisioner.drydock_client.session import KeystoneClient
from drydock_provisioner.util import KeystoneUtils


def get_internal_api_href(ver):
    """Get the internal API href for Drydock API version ``ver``."""

    # TODO(sh8121att) Support versioned service registration
    supported_versions = ['v1.0']

    if ver in supported_versions:
        ks_sess = KeystoneUtils.get_session()
        url = KeystoneClient.get_endpoint(
            "physicalprovisioner", ks_sess=ks_sess, interface='internal')
        return url
    else:
        raise ApiError("API version %s unknown." % ver)

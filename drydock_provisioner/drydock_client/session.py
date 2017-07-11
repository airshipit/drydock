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

class DrydockSession(object):
    """
    A session to the Drydock API maintaining credentials and API options

    :param string host: The Drydock server hostname or IP
    :param int port: The service port, defaults to 9000
    :param string token: Auth token
    :param string marker: (optional) external context marker
    """

    def __init__(self, host=None, port=9000, token=None, marker=None):
        self.__session = requests.Session()
        self.__session.headers.update({'X-Auth-Token': token, 'X-Context-Marker': marker}) 
        self.host = host
        self.port = port
        self.base_url = "http://%s:%d/api/" % (host, port)
        self.token = token
        self.marker = marker

    # TODO Add keystone authentication to produce a token for this session

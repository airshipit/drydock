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
import json
import requests

from .session import DrydockSession

class DrydockClient(object):
    """"
    A client for the Drydock API

    :param string host: Hostname or IP address of Drydock API
    :param string port: Port number of Drydock API
    :param string version: API version to access
    :param string token: Authentication token to use
    :param string marker: (optional) External marker to include with requests
    """

    def __init__(self, host=None, port=9000, version='1.0', token=None, marker=None):
        self.version = version
        self.session = DrydockSession(token=token, ext_marker=marker)
        self.base_url = "http://%s:%d/api/%s/" % (host, port, version)

    def send_get(self, api_url, query=None):
        """
        Send a GET request to Drydock.

        :param string api_url: The URL string following the hostname and API prefix
        :param dict query: A dict of k, v pairs to add to the query string
        :return: A requests.Response object
        """
        resp = requests.get(self.base_url + api_url, params=query)

        return resp

    def send_post(self, api_url, query=None, body=None, data=None):
        """
        Send a POST request to Drydock. If both body and data are specified,
        body will will be used.

        :param string api_url: The URL string following the hostname and API prefix
        :param dict query: A dict of k, v parameters to add to the query string
        :param string body: A string to use as the request body. Will be treated as raw
        :param data: Something json.dumps(s) can serialize. Result will be used as the request body
        :return: A requests.Response object
        """

        if body is not None:
            resp = requests.post(self.base_url + api_url, params=query, data=body)
        else:
            resp = requests.post(self.base_url + api_url, params=query, json=data)

        return resp

    def get_designs(self):
        """
        Get list of Drydock design_ids

        :return: A list of string design_ids
        """
        url = '/designs'

        resp = send_get(url)

        if resp.status_code != 200:
            
        else:
            return resp.json()

    def get_design(self, design_id):

    def create_design(self):

    def get_parts(self, design_id):

    def get_part(self, design_id, kind, key):

    def load_parts(self, design_id, yaml_string=None):

    def get_tasks(self):

    def get_task(self, task_id):

    def create_task(self, design_id, task_action, node_filter=None):


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
"""Test nodes build data API with Postgres backend."""
import pytest
from falcon import testing

import uuid
import datetime
import random

import drydock_provisioner.objects as objects

from drydock_provisioner import policy
from drydock_provisioner.control.api import start_api

import falcon


class TestNodeBuildDataApi():

    def test_read_builddata_all(self, falcontest, seeded_builddata):
        """Test that by default the API returns all build data for a node."""
        url = '/api/v1.0/nodes/foo/builddata'

        # Seed the database with build data
        nodelist = ['foo']
        count = 3
        seeded_builddata(nodelist=nodelist, count=count)

        # TODO(sh8121att) Make fixture for request header forging
        hdr = {
            'Content-Type': 'application/json',
            'X-IDENTITY-STATUS': 'Confirmed',
            'X-USER-NAME': 'Test',
            'X-ROLES': 'admin'
        }

        resp = falcontest.simulate_get(url, headers=hdr)

        assert resp.status == falcon.HTTP_200

        resp_body = resp.json

        assert len(resp_body) == count

    def test_read_builddata_latest(self, falcontest, seeded_builddata):
        """Test that the ``latest`` parameter works."""
        url = '/api/v1.0/nodes/foo/builddata'

        req_hdr = {
            'Content-Type': 'application/json',
            'X-IDENTITY-STATUS': 'Confirmed',
            'X-USER-NAME': 'Test',
            'X-ROLES': 'admin',
        }

        # Seed the database with build data
        nodelist = ['foo']
        generatorlist = ['hello', 'hello', 'bye']
        count = 3
        seeded_builddata(nodelist=nodelist,
                         generatorlist=generatorlist,
                         count=count,
                         random_dates=True)

        resp = falcontest.simulate_get(url,
                                       headers=req_hdr,
                                       query_string="latest=true")

        assert resp.status == falcon.HTTP_200

        resp_body = resp.json

        # Should only be a single instance for each unique generator
        assert len(resp_body) == len(set(generatorlist))

    @pytest.fixture()
    def seeded_builddata(self, blank_state):
        """Provide function to seed the database with build data."""

        def seed_build_data(nodelist=['foo'],
                            tasklist=None,
                            generatorlist=None,
                            count=1,
                            random_dates=True):
            """Seed the database with ``count`` build data elements for each node.

            If tasklist is specified, it should be a list of length ``count`` such that
            as build_data are added for a node, each task_id will be used one for each node

            :param nodelist: list of string nodenames for build data
            :param tasklist: list of uuid.UUID IDs for task. If omitted, uuids will be generated
            :param gneratorlist: list of string generatos to assign to build data. If omitted, 'hello_world'
                                 is used.
            :param count: number build data elements to create for each node
            :param random_dates: whether to generate random dates in the past 180 days or create each
                                 build data element with utcnow()
            """
            for n in nodelist:
                for i in range(count):
                    if random_dates:
                        collected_date = datetime.datetime.utcnow(
                        ) - datetime.timedelta(days=random.randint(1, 180))
                    else:
                        collected_date = None
                    if tasklist:
                        task_id = tasklist[i]
                    else:
                        task_id = uuid.uuid4()
                    if generatorlist:
                        generator = generatorlist[i]
                    else:
                        generator = 'hello_world'
                    bd = objects.BuildData(node_name=n,
                                           task_id=task_id,
                                           generator=generator,
                                           data_format='text/plain',
                                           collected_date=collected_date,
                                           data_element='Hello World!')
                    blank_state.post_build_data(bd)
                    i = i + 1

        return seed_build_data

    # TODO(sh8121att) Make this a general fixture in conftest.py
    @pytest.fixture()
    def falcontest(self, drydock_state, deckhand_ingester,
                   deckhand_orchestrator):
        """Create a test harness for the Falcon API framework."""
        policy.policy_engine = policy.DrydockPolicy()
        policy.policy_engine.register_policy()

        return testing.TestClient(
            start_api(state_manager=drydock_state,
                      ingester=deckhand_ingester,
                      orchestrator=deckhand_orchestrator))

    @policy.ApiEnforcer('physical_provisioner:read_task')
    def target_function(self, req, resp):
        return True

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
"""Test orchestrator leadership organization via Postgres."""
import uuid
import time


class TestPostgres(object):
    def test_claim_leadership(self, blank_state):
        """Test that a node can claim leadership.

        First test claiming leadership with an empty table, simulating startup
        Second test that an immediate follow-up claim is denied
        Third test that a usurping claim after the grace period succeeds
        """
        ds = blank_state

        first_leader = uuid.uuid4()
        second_leader = uuid.uuid4()

        print("Claiming leadership for %s" % str(first_leader.bytes))
        crown = ds.claim_leadership(first_leader)

        assert crown

        print("Claiming leadership for %s" % str(second_leader.bytes))
        crown = ds.claim_leadership(second_leader)

        assert crown is False

        time.sleep(20)

        print(
            "Claiming leadership for %s after 20s" % str(second_leader.bytes))
        crown = ds.claim_leadership(second_leader)

        assert crown

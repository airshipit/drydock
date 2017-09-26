import pytest

import logging
import uuid
import time

from oslo_config import cfg

import drydock_provisioner.objects as objects
import drydock_provisioner.config as config

from drydock_provisioner.statemgmt.state import DrydockState


class TestPostgres(object):
    def test_claim_leadership(self, setup):
        """Test that a node can claim leadership.

        First test claiming leadership with an empty table, simulating startup
        Second test that an immediate follow-up claim is denied
        Third test that a usurping claim after the grace period succeeds
        """
        ds = DrydockState()

        first_leader = uuid.uuid4()
        second_leader = uuid.uuid4()

        print("Claiming leadership for %s" % str(first_leader.bytes))
        crown = ds.claim_leadership(first_leader)

        assert crown == True

        print("Claiming leadership for %s" % str(second_leader.bytes))
        crown = ds.claim_leadership(second_leader)

        assert crown == False

        time.sleep(20)

        print(
            "Claiming leadership for %s after 20s" % str(second_leader.bytes))
        crown = ds.claim_leadership(second_leader)

        assert crown == True

    @pytest.fixture(scope='module')
    def setup(self):
        objects.register_all()
        logging.basicConfig()

        req_opts = {
            'default': [cfg.IntOpt('leader_grace_period')],
            'database': [cfg.StrOpt('database_connect_string')],
            'logging': [
                cfg.StrOpt('global_logger_name', default='drydock'),
            ]
        }

        for k, v in req_opts.items():
            config.config_mgr.conf.register_opts(v, group=k)

        config.config_mgr.conf([])
        config.config_mgr.conf.set_override(
            name="database_connect_string",
            group="database",
            override=
            "postgresql+psycopg2://drydock:drydock@localhost:5432/drydock")
        config.config_mgr.conf.set_override(
            name="leader_grace_period", group="default", override=15)

        return

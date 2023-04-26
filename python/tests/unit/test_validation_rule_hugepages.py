"""Test Validation Rule for Hugepages"""

import logging

import drydock_provisioner.config as config

from drydock_provisioner.orchestrator.orchestrator import Orchestrator
from drydock_provisioner.orchestrator.validations.hugepages_validity import HugepagesValidity

LOG = logging.getLogger(__name__)


class TestValidPlatform(object):

    def test_valid_platform(self, deckhand_ingester, drydock_state,
                            input_files):
        input_file = input_files.join("validation.yaml")
        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(state_manager=drydock_state,
                            ingester=deckhand_ingester,
                            enabled_drivers=config.config_mgr.conf.plugins)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        validator = HugepagesValidity()
        message_list = validator.execute(site_design, orchestrator=orch)

        for r in message_list:
            LOG.debug(r.to_dict())

        msg = message_list[0].to_dict()

        assert msg.get('error') is False
        assert len(message_list) == 1

    def test_invalid_hugepages(self, deckhand_ingester, drydock_state,
                               input_files):
        """Test that a design with incorrect hugepages configuration."""

        input_file = input_files.join("invalid_hugepages.yaml")
        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(state_manager=drydock_state,
                            ingester=deckhand_ingester,
                            enabled_drivers=config.config_mgr.conf.plugins)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        validator = HugepagesValidity()
        message_list = validator.execute(site_design)
        assert len(message_list) > 0

        for msg in message_list:
            msg = msg.to_dict()
            LOG.debug(msg)
            assert len(msg.get('documents', [])) > 0
            assert msg.get('error') is True

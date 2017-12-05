"""Test Validation Rule Rational Network Trunking"""
from drydock_provisioner.orchestrator.orchestrator import Orchestrator
from drydock_provisioner.orchestrator.validations.validator import Validator
import re


class TestStorageSizing(object):
    def test_storage_sizing(self, deckhand_ingester, drydock_state, input_files):

        input_file = input_files.join("storage_sizing.yaml")
        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(state_manager=drydock_state, ingester=deckhand_ingester)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        message_list = Validator.storage_sizing(site_design)
        msg = message_list[0].to_dict()

        assert len(message_list) == 1
        assert msg.get('message') == 'Storage Sizing'
        assert msg.get('error') is False

    def test_invalid_storage_sizing_negitive(self, deckhand_ingester, drydock_state, input_files):

        input_file = input_files.join("invalid_storage_sizing_negitive.yaml")
        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(state_manager=drydock_state, ingester=deckhand_ingester)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        message_list = Validator.storage_sizing(site_design)

        regex = re.compile('Storage Sizing Error: Storage .+ size is < 0 on Baremetal Node .+')

        assert len(message_list) == 4
        for msg in message_list:
            msg = msg.to_dict()
            assert regex.match(msg.get('message')) is not None
            assert msg.get('error') is True

    def test_invalid_storage_sizing_large(self, deckhand_ingester, drydock_state, input_files):

        input_file = input_files.join("invalid_storage_sizing_large.yaml")
        design_ref = "file://%s" % str(input_file)

        orch = Orchestrator(state_manager=drydock_state, ingester=deckhand_ingester)

        status, site_design = Orchestrator.get_effective_site(orch, design_ref)

        message_list = Validator.storage_sizing(site_design)

        regex = re.compile('Storage Sizing Error: Storage .+ size is greater than 99 on Baremetal Node .+')

        assert len(message_list) == 4
        for msg in message_list:
            msg = msg.to_dict()
            assert regex.match(msg.get('message')) is not None
            assert msg.get('error') is True

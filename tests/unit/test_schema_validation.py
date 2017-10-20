
import yaml
import jsonschema
import pkg_resources
import os
import shutil
import pytest

from jsonschema.exceptions import ValidationError

class BaseSchemaValidationTest(object):
    def _test_validate(self, schema, expect_failure, input_files, input):
        """validates input yaml against schema.

        :param schema: schema yaml file
        :param expect_failure: should the validation pass or fail.
        :param input_files: pytest fixture used to access the test input files
        :param input: test input yaml doc filename"""
        schema_dir = pkg_resources.resource_filename('drydock_provisioner',
                                                     'schemas')
        schema_filename = os.path.join(schema_dir, schema)
        schema_file = open(schema_filename, 'r')
        schema = yaml.safe_load(schema_file)

        input_file = input_files.join(input)
        instance_file = open(str(input_file), 'r')
        instance = yaml.safe_load(instance_file)

        if expect_failure:
            with pytest.raises(ValidationError):
                jsonschema.validate(instance['spec'], schema['data'])
        else:
            jsonschema.validate(instance['spec'], schema['data'])


class TestValidation(BaseSchemaValidationTest):
    def test_validate_baremetalNode(self, input_files):
        self._test_validate('baremetalNode.yaml', False, input_files, "baremetalNode.yaml")

    def test_validate_baremetalNode2(self, input_files):
        self._test_validate('baremetalNode.yaml', False, input_files, "baremetalNode2.yaml")

    def test_invalidate_baremetalNode(self, input_files):
        self._test_validate('baremetalNode.yaml', True, input_files, "invalid_baremetalNode.yaml")

    def test_invalidate_baremetalNode2(self, input_files):
        self._test_validate('baremetalNode.yaml', True, input_files, "invalid_baremetalNode2.yaml")

    def test_validate_hardwareProfile(self, input_files):
        self._test_validate('hardwareProfile.yaml', False, input_files, "hardwareProfile.yaml")

    def test_invalidate_hardwareProfile(self, input_files):
        self._test_validate('hardwareProfile.yaml', True, input_files, "invalid_hardwareProfile.yaml")

    def test_validate_hostProfile(self, input_files):
        self._test_validate('hostProfile.yaml', False, input_files, "hostProfile.yaml")

    def test_validate_hostProfile2(self, input_files):
        self._test_validate('hostProfile.yaml', False, input_files, "hostProfile2.yaml")

    def test_invalidate_hostProfile(self, input_files):
        self._test_validate('hostProfile.yaml', True, input_files, "invalid_hostProfile.yaml")

    def test_invalidate_hostProfile2(self, input_files):
        self._test_validate('hostProfile.yaml', True, input_files, "invalid_hostProfile2.yaml")

    def test_validate_network(self, input_files):
        self._test_validate('network.yaml', False, input_files, "network.yaml")

    def test_validate_network2(self, input_files):
        self._test_validate('network.yaml', False, input_files, "network2.yaml")

    def test_validate_network3(self, input_files):
        self._test_validate('network.yaml', False, input_files, "network3.yaml")

    def test_validate_network4(self, input_files):
        self._test_validate('network.yaml', False, input_files, "network4.yaml")

    def test_validate_network5(self, input_files):
        self._test_validate('network.yaml', False, input_files, "network5.yaml")

    def test_invalidate_network(self, input_files):
        self._test_validate('network.yaml', True, input_files, "invalid_network.yaml")

    def test_invalidate_network2(self, input_files):
        self._test_validate('network.yaml', True, input_files, "invalid_network2.yaml")

    def test_invalidate_network3(self, input_files):
        self._test_validate('network.yaml', True, input_files, "invalid_network3.yaml")

    def test_invalidate_network4(self, input_files):
        self._test_validate('network.yaml', True, input_files, "invalid_network4.yaml")

    def test_invalidate_network5(self, input_files):
        self._test_validate('network.yaml', True, input_files, "invalid_network5.yaml")

    def test_validate_networkLink(self, input_files):
        self._test_validate('networkLink.yaml', False, input_files, "networkLink.yaml")

    def test_validate_networkLink2(self, input_files):
        self._test_validate('networkLink.yaml', False, input_files, "networkLink2.yaml")

    def test_validate_networkLink3(self, input_files):
        self._test_validate('networkLink.yaml', False, input_files, "networkLink3.yaml")

    def test_invalidate_networkLink(self, input_files):
        self._test_validate('networkLink.yaml', True, input_files, "invalid_networkLink.yaml")

    def test_invalidate_networkLink2(self, input_files):
        self._test_validate('networkLink.yaml', True, input_files, "invalid_networkLink2.yaml")

    def test_invalidate_networkLink3(self, input_files):
        self._test_validate('networkLink.yaml', True, input_files, "invalid_networkLink3.yaml")

    def test_validate_region(self, input_files):
        self._test_validate('region.yaml', False, input_files, "region.yaml")

    def test_invalidate_region(self, input_files):
        self._test_validate('region.yaml', True, input_files, "invalid_region.yaml")

    def test_validate_rack(self, input_files):
        self._test_validate('rack.yaml', False, input_files, "rack.yaml")

    def test_invalidate_rack(self, input_files):
        self._test_validate('rack.yaml', True, input_files, "invalid_rack.yaml")

    @pytest.fixture(scope='module')
    def input_files(self, tmpdir_factory, request):
        tmpdir = tmpdir_factory.mktemp('data')
        samples_dir = os.path.dirname(str(
            request.fspath)) + "/" + "../yaml_samples"
        samples = os.listdir(samples_dir)

        for f in samples:
            src_file = samples_dir + "/" + f
            dst_file = str(tmpdir) + "/" + f
            shutil.copyfile(src_file, dst_file)

        return tmpdir

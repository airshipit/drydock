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


class DesignError(Exception):
    """
    **Message:** *Invalid Network model*.

    **Troubleshoot:**

    **Message:** *Network <network_key> not found in design state*.

    **Troubleshoot:**

    **Message:** *Design <design_id> not found*.

    **Troubleshoot:**
    """
    pass


class IngesterError(DesignError):
    """
    **Message:** *Error parsing YAML <various>*.

    **Troubleshoot:**
    """
    pass


class InvalidDesignReference(DesignError):
    """
    **Message:** *Invalid reference scheme <design_url.scheme>: no handler*.

    **Troubleshoot:**

    **Message:** *Cannot resolve design reference <design_ref>: unable to
    parse as valid URI*.

    **Troubleshoot:**
    """
    pass


class UnsupportedDocumentType(DesignError):
    """
    **Message:** *Site definition document in an unknown format*.

    **Troubleshoot:**
    """
    pass


class HugepageConfNotFound(DesignError):
    """
    **Message:** *Hugepage configuration not found*.

    **Troubleshoot:** *Define the hugepage configuration in the HardwareProfile*.
    """
    pass


class CpuSetNotFound(DesignError):
    """
    **Message:** *CPU set not found*.

    **Troubleshoot:** *Define the CPU set in the HardwareProfile*.
    """
    pass


class InvalidParameterReference(DesignError):
    """
    **Message:** *Invalid configuration specified*.

    **Troubleshoot:** *Only ``cpuset`` and ``hugepages`` can be referenced*.

    **Message:** *Invalid field specified*.

    **Troubleshoot:** *For hugepages, only fields ``size`` and ``count`` are valid*.
    """
    pass


class StateError(Exception):
    pass


class TaskNotFoundError(StateError):
    pass


class OrchestratorError(Exception):
    """
    **Message:** *Could find task <task_id>*.

    **Troubleshoot:**

    **Message:** *Unable to render effective site design.*

    **Troubleshoot:**

    **Message:** *Cannot specify both failures and successes*.

    **Troubleshoot:**

    **Message:** *Unknow filter set type*.

    **Troubleshoot:**

    **Message:** *Error processing node filter*.

    **Troubleshoot:**

    **Message:** *Orchestrator requires instantiated state manager and
    ingester*.

    **Troubleshoot:**
    """
    pass


class MaxRetriesReached(OrchestratorError):
    """
    **Message:** *Retries reached max attempts*.

    **Troubleshoot:**
    """
    pass


class CollectSubtaskTimeout(OrchestratorError):
    pass


class TransientOrchestratorError(OrchestratorError):
    pass


class PersistentOrchestratorError(OrchestratorError):
    pass


class BootactionError(Exception):
    pass


class UnknownPipelineSegment(BootactionError):
    """
    **Message:** *Bootaction pipeline segment <various> unknown*.

    **Troubleshoot:**
    """
    pass


class PipelineFailure(BootactionError):
    """
    **Message:** *Error when running bootaction pipeline segment <various>*.

    **Troubleshoot:**
    """
    pass


class InvalidAssetLocation(BootactionError):
    """
    **Message:** *Unable to resolve asset reference <various>*.

    **Troubleshoot:**
    """
    pass


class InvalidPackageListFormat(BootactionError):
    """
    **Message:** *Invalid package list format.*.

    **Troubleshoot: A packagelist should be valid YAML
                    document that is a mapping with keys being
                    Debian package names and values being version
                    specifiers. Null values are valid and indicate no
                    version requirement.
    """
    pass


class BuildDataError(Exception):
    """
    **Message:** *Error saving build data - data_element type <data_element>
    could not be cast to string*.

    **Troubleshoot:**

    **Message:** *Error selecting build data*.

    **Troubleshoot:**
    """
    pass


class DriverError(Exception):
    """
    **Message:** *Invalid task <task_id>*.

    **Troubleshoot:**

    **Message:** *Driver <driver_desc> doesn't support task action <action>*.

    **Troubleshoot:**

    **Message:** *Fabric not found in MaaS for fabric_id <fabric_id>,
    fabric_name <fabric_name>*.

    **Troubeshoot:**

    **Message:** *Cannot locate untagged VLAN on fabric <fabric_id>*.

    **Troubleshoot:**

    **Message:** *Error retrieving node/tag pairs, received HTTP
    <resp.status_code> from MaaS*.

    **Troubleshoot:**

    **Message:** *Tag <res.name> already exists*.

    **Troubleshoot:**

    **Message:** *Error resetting network on node <resource_id>:
    <resp.status_code>, <resp.text>*.

    **Troubleshoot:**

    **Message:** *"Error: cannot find storage device <root_device> to set as
    root device*.

    **Troubleshoot:**

    **Message:** *Error: failed configuring node <resource_id> storage layout:
    <various>*.

    **Troubleshoot:**

    **Message:** *Error commissioning node, received HTTP <resp.status_code>
    from MaaS*.

    **Troubleshoot:**

    **Message:** *Error deploying node, received HTTP <resp.status_code> from
    MaaS*.

    **Troubleshoot:**

    **Message:** *Error setting node metadata, received HTTP <resp.status_code>
    from MaaS*.

    **Troubleshoot:**

    **Message:** *Node <node_name> not found*.

    **Troubleshoot:**

    **Message:** *Node <node_name> status '<node.status_name>' does not allow
    deployment, should be 'Ready'*.

    **Troubleshoot:**

    **Message:** *Error acquiring node, MaaS returned <resp.status_code>*.

    **Troubleshoot:**

    **Message:** *Failed updating MAAS url <url> - return code
    <resp.status_code>*.

    **Troubleshoot:**

    **Message:** *Node OOB type is not IPMI*.

    **Troubleshoot:**

    **Message:** *Node <node_name> has no IPMI address*.

    **Troubleshoot:**

    **Message:** *IPMI command failed*.

    **Troubleshoot:**

    **Message:** *Unsupported action <task_action> for driver <driver_desc>*.

    **Troubleshoot:**

    **Message:** *Failed updating MAAS url <url> - return code
    <resp.status_code> <resp.text>*

    **Troubleshoot:**

    **Message:** *Invalid JSON for class <class_name>*.

    **Troubleshoot:**

    **Message:** *Error: Could not create logical volume <various>*.

    **Troubleshoot:**

    **Message:** *Error: Could not delete logical volume <various>*.

    **Troubleshoot:**

    **Message:** *Inconsistent data from MaaS*.

    **Troubleshoot:**
    """
    pass


class TransientDriverError(DriverError):
    """
    **Message:** *Timeout connection to MaaS*

    **Troubleshoot:** *Coming Soon*

    **Message:** *Recieved 50x error from MaaS*

    **Troubleshoot:** *Coming Soon*
    """
    pass


class PersistentDriverError(DriverError):
    """
    **Message:** *Recieved unexpected error from MaaS*

    **Troubleshoot:** *Coming Soon*

    **Message:** *Error accessing MaaS: <details>*

    **Troubleshoot:** *Coming Soon*

    **Message:** *MaaS API Authentication Failed*

    **Troubleshoot:** *Coming Soon*
    """
    pass


class NotEnoughStorage(DriverError):
    """
    **Message:** *The calcuted size is not available.*

    **Troubleshoot:** *Coming Soon*
    """
    pass


class InvalidSizeFormat(DriverError):
    """
    **Message:** *Invalid size string format: <size of string>*

    **Troubleshoot:** *Coming Soon*

    **Message:** *Sizes using the ">" or "%" format must specify a block device
    or volume group context*

    **Troubleshoot:** *Coming Soon*
    """
    pass


class ApiError(Exception):

    def __init__(self, msg, code=500):
        super().__init__(msg)
        self.message = msg
        self.status_code = code

    def to_json(self):
        err_dict = {'error': self.message, 'type': self.__class__.__name__}
        return json.dumps(err_dict)


class InvalidFormat(ApiError):
    """
    **Message:** *Invalid JSON in body: <path>*

    **Code:** 400

    **Troubleshoot:** *Coming Soon*
    """

    def __init__(self, msg, code=400):
        super(InvalidFormat, self).__init__(msg, code=code)


class ClientError(ApiError):
    """
    **Message:** *Error - recieved <status code>: <details>*

    **Code:** 500

    **Troubleshoot:** *Coming Soon*
    """

    def __init__(self, msg, code=500):
        super().__init__(msg)


class ClientUnauthorizedError(ClientError):
    """
    **Message:** *Unauthorized access to <url>, include valid token.*

    **Code:** 401

    **Troubleshoot:** *Try requesting a new token.*
    """

    def __init__(self, msg):
        super().__init__(msg, code=401)


class ClientForbiddenError(ClientError):
    """
    **Message:** *Forbidden access to <url>.*

    **Code:** 403

    **Troubleshoot:** *Coming Soon*
    """

    def __init__(self, msg):
        super().__init__(msg, code=403)

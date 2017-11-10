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

from oslo_versionedobjects import fields


class BaseDrydockEnum(fields.Enum):
    def __init__(self):
        super(BaseDrydockEnum, self).__init__(valid_values=self.__class__.ALL)


class OrchestratorAction(BaseDrydockEnum):
    # Orchestrator actions
    Noop = 'noop'
    ValidateDesign = 'validate_design'
    VerifySite = 'verify_site'
    PrepareSite = 'prepare_site'
    VerifyNodes = 'verify_nodes'
    PrepareNodes = 'prepare_nodes'
    DeployNodes = 'deploy_nodes'
    DestroyNodes = 'destroy_nodes'
    BootactionReport = 'bootaction_report'

    # OOB driver actions
    ValidateOobServices = 'validate_oob_services'
    ConfigNodePxe = 'config_node_pxe'
    SetNodeBoot = 'set_node_boot'
    PowerOffNode = 'power_off_node'
    PowerOnNode = 'power_on_node'
    PowerCycleNode = 'power_cycle_node'
    InterrogateOob = 'interrogate_oob'

    # Node driver actions
    ValidateNodeServices = 'validate_node_services'
    CreateNetworkTemplate = 'create_network_template'
    CreateStorageTemplate = 'create_storage_template'
    CreateBootMedia = 'create_boot_media'
    ConfigureUserCredentials = 'configure_user_credentials'
    PrepareHardwareConfig = 'prepare_hardware_config'
    IdentifyNode = 'identify_node'
    ConfigureHardware = 'configure_hardware'
    InterrogateNode = 'interrogate_node'
    ApplyNodeNetworking = 'apply_node_networking'
    ApplyNodeStorage = 'apply_node_storage'
    ApplyNodePlatform = 'apply_node_platform'
    DeployNode = 'deploy_node'
    DestroyNode = 'destroy_node'

    # Network driver actions
    ValidateNetworkServices = 'validate_network_services'
    InterrogatePort = 'interrogate_port'
    ConfigurePortProvisioning = 'config_port_provisioning'
    ConfigurePortProduction = 'config_port_production'

    ALL = (Noop, ValidateDesign, VerifySite, PrepareSite, VerifyNodes,
           PrepareNodes, DeployNodes, BootactionReport, DestroyNodes,
           ConfigNodePxe, SetNodeBoot, PowerOffNode, PowerOnNode,
           PowerCycleNode, InterrogateOob, CreateNetworkTemplate,
           CreateStorageTemplate, CreateBootMedia, PrepareHardwareConfig,
           ConfigureHardware, InterrogateNode, ApplyNodeNetworking,
           ApplyNodeStorage, ApplyNodePlatform, DeployNode, DestroyNode)


class OrchestratorActionField(fields.BaseEnumField):
    AUTO_TYPE = OrchestratorAction()


class ActionResult(BaseDrydockEnum):
    Incomplete = 'incomplete'
    Success = 'success'
    PartialSuccess = 'partial_success'
    Failure = 'failure'

    ALL = (Incomplete, Success, PartialSuccess, Failure)


class ActionResultField(fields.BaseEnumField):
    AUTO_TYPE = ActionResult()


class TaskStatus(BaseDrydockEnum):
    Requested = 'requested'
    Queued = 'queued'
    Running = 'running'
    Terminating = 'terminating'
    Terminated = 'terminated'
    Complete = 'complete'

    ALL = (Requested, Queued, Running, Terminating, Terminated, Complete)


class TaskStatusField(fields.BaseEnumField):
    AUTO_TYPE = TaskStatus()


class ModelSource(BaseDrydockEnum):
    Designed = 'designed'
    Compiled = 'compiled'
    Build = 'build'

    ALL = (Designed, Compiled, Build)


class ModelSourceField(fields.BaseEnumField):
    AUTO_TYPE = ModelSource()


class SiteStatus(BaseDrydockEnum):
    Unknown = 'unknown'
    DesignStarted = 'design_started'
    DesignAvailable = 'design_available'
    DesignValidated = 'design_validated'
    Deploying = 'deploying'
    Deployed = 'deployed'
    DesignUpdated = 'design_updated'

    ALL = (Unknown, Deploying, Deployed)


class SiteStatusField(fields.BaseEnumField):
    AUTO_TYPE = SiteStatus()


class NodeStatus(BaseDrydockEnum):
    Unknown = 'unknown'
    Designed = 'designed'
    Compiled = 'compiled'  # Node attributes represent effective config after inheritance/merge
    Present = 'present'  # IPMI access verified
    BasicVerifying = 'basic_verifying'  # Base node verification in process
    FailedBasicVerify = 'failed_basic_verify'  # Base node verification failed
    BasicVerified = 'basic_verified'  # Base node verification successful
    Preparing = 'preparing'  # Node preparation in progress
    FailedPrepare = 'failed_prepare'  # Node preparation failed
    Prepared = 'prepared'  # Node preparation complete
    FullyVerifying = 'fully_verifying'  # Node full verification in progress
    FailedFullVerify = 'failed_full_verify'  # Node full verification failed
    FullyVerified = 'fully_verified'  # Deeper verification successful
    Deploying = 'deploy'  # Node deployment in progress
    FailedDeploy = 'failed_deploy'  # Node deployment failed
    Deployed = 'deployed'  # Node deployed successfully
    Bootstrapping = 'bootstrapping'  # Node bootstrapping
    FailedBootstrap = 'failed_bootstrap'  # Node bootstrapping failed
    Bootstrapped = 'bootstrapped'  # Node fully bootstrapped
    Complete = 'complete'  # Node is complete

    ALL = (Unknown, Designed, Compiled, Present, BasicVerifying,
           FailedBasicVerify, BasicVerified, Preparing, FailedPrepare,
           Prepared, FullyVerifying, FailedFullVerify, FullyVerified,
           Deploying, FailedDeploy, Deployed, Bootstrapping, FailedBootstrap,
           Bootstrapped, Complete)


class NodeStatusField(fields.BaseEnumField):
    AUTO_TYPE = NodeStatus()


class NetworkLinkBondingMode(BaseDrydockEnum):
    Disabled = 'disabled'
    LACP = '802.3ad'
    RoundRobin = 'balanced-rr'
    Standby = 'active-backup'

    ALL = (Disabled, LACP, RoundRobin, Standby)


class NetworkLinkBondingModeField(fields.BaseEnumField):
    AUTO_TYPE = NetworkLinkBondingMode()


class NetworkLinkTrunkingMode(BaseDrydockEnum):
    Disabled = 'disabled'
    Tagged = '802.1q'

    ALL = (Disabled, Tagged)


class NetworkLinkTrunkingModeField(fields.BaseEnumField):
    AUTO_TYPE = NetworkLinkTrunkingMode()

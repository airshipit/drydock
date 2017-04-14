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
from enum import Enum, unique

@unique
class OrchestratorAction(Enum):
    Noop = 'noop'
    ValidateDesign = 'validate_design'
    VerifySite = 'verify_site'
    PrepareSite = 'prepare_site'
    VerifyNode = 'verify_node'
    PrepareNode = 'prepare_node'
    DeployNode = 'deploy_node'
    DestroyNode = 'destroy_node'

@unique
class ActionResult(Enum):
    Success = 'success'
    PartialSuccess = 'partial_success'
    Failure = 'failure'
    DependentFailure = 'dependent_failure'

@unique
class SiteStatus(Enum):
    Unknown = 'unknown'
    DesignStarted = 'design_started'
    DesignAvailable = 'design_available'
    DesignValidated = 'design_validated'
    Deploying = 'deploying'
    Deployed = 'deployed'
    DesignUpdated = 'design_updated'

@unique
class NodeStatus(Enum):
    Unknown = 'unknown'
    Designed = 'designed'
    Present = 'present' # IPMI access verified
    BasicVerifying = 'basic_verifying' # Base node verification in process
    FailedBasicVerify = 'failed_basic_verify' # Base node verification failed
    BasicVerified = 'basic_verified' # Base node verification successful
    Preparing = 'preparing' # Node preparation in progress
    FailedPrepare = 'failed_prepare' # Node preparation failed
    Prepared = 'prepared' # Node preparation complete
    FullyVerifying = 'fully_verifying' # Node full verification in progress
    FailedFullVerify = 'failed_full_verify' # Node full verification failed
    FullyVerified = 'fully_verified' # Deeper verification successful
    Deploying  = 'deploy' # Node deployment in progress
    FailedDeploy = 'failed_deploy' # Node deployment failed
    Deployed = 'deployed' # Node deployed successfully
    Bootstrapping = 'bootstrapping' # Node bootstrapping
    FailedBootstrap = 'failed_bootstrap' # Node bootstrapping failed
    Bootstrapped = 'bootstrapped' # Node fully bootstrapped
    Complete = 'complete' # Node is complete

@unique
class TaskStatus(Enum):
    Created = 'created'
    Waiting = 'waiting'
    Running = 'running'
    Stopping = 'stopping'
    Terminated = 'terminated'
    Errored = 'errored'
    Complete = 'complete'
    Stopped = 'stopped'
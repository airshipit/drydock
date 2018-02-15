# Copyright 2017 AT&T Intellectual Property.  All other rights reserved.
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
"""Task driver for completing node provisioning with Canonical MaaS 2.2+."""

import logging
import uuid
import concurrent.futures

from oslo_config import cfg

import drydock_provisioner.error as errors
import drydock_provisioner.objects.fields as hd_fields
import drydock_provisioner.config as config

from drydock_provisioner.drivers.node.driver import NodeDriver
from drydock_provisioner.drivers.node.maasdriver.api_client import MaasRequestFactory
from drydock_provisioner.drivers.node.maasdriver.models.boot_resource import BootResources

from .actions.node import ValidateNodeServices
from .actions.node import CreateStorageTemplate
from .actions.node import CreateBootMedia
from .actions.node import PrepareHardwareConfig
from .actions.node import InterrogateNode
from .actions.node import DestroyNode
from .actions.node import CreateNetworkTemplate
from .actions.node import ConfigureUserCredentials
from .actions.node import IdentifyNode
from .actions.node import ConfigureHardware
from .actions.node import ApplyNodeNetworking
from .actions.node import ApplyNodePlatform
from .actions.node import ApplyNodeStorage
from .actions.node import DeployNode


class MaasNodeDriver(NodeDriver):
    maasdriver_options = [
        cfg.StrOpt(
            'maas_api_key', help='The API key for accessing MaaS',
            secret=True),
        cfg.StrOpt('maas_api_url', help='The URL for accessing MaaS API'),
        cfg.IntOpt(
            'poll_interval',
            default=10,
            help='Polling interval for querying MaaS status in seconds'),
    ]

    driver_name = 'maasdriver'
    driver_key = 'maasdriver'
    driver_desc = 'MaaS Node Provisioning Driver'

    action_class_map = {
        hd_fields.OrchestratorAction.ValidateNodeServices:
        ValidateNodeServices,
        hd_fields.OrchestratorAction.CreateStorageTemplate:
        CreateStorageTemplate,
        hd_fields.OrchestratorAction.CreateBootMedia:
        CreateBootMedia,
        hd_fields.OrchestratorAction.PrepareHardwareConfig:
        PrepareHardwareConfig,
        hd_fields.OrchestratorAction.InterrogateNode:
        InterrogateNode,
        hd_fields.OrchestratorAction.DestroyNode:
        DestroyNode,
        hd_fields.OrchestratorAction.CreateNetworkTemplate:
        CreateNetworkTemplate,
        hd_fields.OrchestratorAction.ConfigureUserCredentials:
        ConfigureUserCredentials,
        hd_fields.OrchestratorAction.IdentifyNode:
        IdentifyNode,
        hd_fields.OrchestratorAction.ConfigureHardware:
        ConfigureHardware,
        hd_fields.OrchestratorAction.ApplyNodeNetworking:
        ApplyNodeNetworking,
        hd_fields.OrchestratorAction.ApplyNodePlatform:
        ApplyNodePlatform,
        hd_fields.OrchestratorAction.ApplyNodeStorage:
        ApplyNodeStorage,
        hd_fields.OrchestratorAction.DeployNode:
        DeployNode,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        cfg.CONF.register_opts(
            MaasNodeDriver.maasdriver_options, group=MaasNodeDriver.driver_key)

        self.logger = logging.getLogger(
            cfg.CONF.logging.nodedriver_logger_name)

    def execute_task(self, task_id):
        # actions that should be threaded for execution
        threaded_actions = [
            hd_fields.OrchestratorAction.InterrogateNode,
            hd_fields.OrchestratorAction.DestroyNode,
            hd_fields.OrchestratorAction.IdentifyNode,
            hd_fields.OrchestratorAction.ConfigureHardware,
            hd_fields.OrchestratorAction.ApplyNodeNetworking,
            hd_fields.OrchestratorAction.ApplyNodeStorage,
            hd_fields.OrchestratorAction.ApplyNodePlatform,
            hd_fields.OrchestratorAction.DeployNode
        ]

        action_timeouts = {
            hd_fields.OrchestratorAction.IdentifyNode:
            config.config_mgr.conf.timeouts.identify_node,
            hd_fields.OrchestratorAction.ConfigureHardware:
            config.config_mgr.conf.timeouts.configure_hardware,
            hd_fields.OrchestratorAction.DeployNode:
            config.config_mgr.conf.timeouts.deploy_node,
        }

        task = self.state_manager.get_task(task_id)

        if task is None:
            raise errors.DriverError("Invalid task %s" % (task_id))

        if task.action not in self.supported_actions:
            raise errors.DriverError(
                "Driver %s doesn't support task action %s" % (self.driver_desc,
                                                              task.action))

        task.set_status(hd_fields.TaskStatus.Running)
        task.save()

        if task.action in threaded_actions:
            if task.retry > 0:
                msg = "Retrying task %s on previous failed entities." % str(
                    task.get_id())
                task.add_status_msg(
                    msg=msg,
                    error=False,
                    ctx=str(task.get_id()),
                    ctx_type='task')
                target_nodes = self.orchestrator.get_target_nodes(
                    task, failures=True)
            else:
                target_nodes = self.orchestrator.get_target_nodes(task)

            with concurrent.futures.ThreadPoolExecutor(max_workers=16) as e:
                subtask_futures = dict()
                for n in target_nodes:
                    maas_client = MaasRequestFactory(
                        config.config_mgr.conf.maasdriver.maas_api_url,
                        config.config_mgr.conf.maasdriver.maas_api_key)
                    nf = self.orchestrator.create_nodefilter_from_nodelist([n])
                    subtask = self.orchestrator.create_task(
                        design_ref=task.design_ref,
                        action=task.action,
                        node_filter=nf,
                        retry=task.retry)
                    task.register_subtask(subtask)

                    action = self.action_class_map.get(task.action, None)(
                        subtask,
                        self.orchestrator,
                        self.state_manager,
                        maas_client=maas_client)
                    subtask_futures[subtask.get_id().bytes] = e.submit(
                        action.start)

                timeout = action_timeouts.get(
                    task.action,
                    config.config_mgr.conf.timeouts.drydock_timeout)
                finished, running = concurrent.futures.wait(
                    subtask_futures.values(), timeout=(timeout * 60))

            for t, f in subtask_futures.items():
                if not f.done():
                    task.add_status_msg(
                        "Subtask %s timed out before completing.",
                        error=True,
                        ctx=str(uuid.UUID(bytes=t)),
                        ctx_type='task')
                    task.failure()
                else:
                    if f.exception():
                        self.logger.error(
                            "Uncaught exception in subtask %s." % str(
                                uuid.UUID(bytes=t)),
                            exc_info=f.exception())
                        task.failure()
            task.bubble_results()
            task.align_result()
        else:
            try:
                maas_client = MaasRequestFactory(
                    config.config_mgr.conf.maasdriver.maas_api_url,
                    config.config_mgr.conf.maasdriver.maas_api_key)
                action = self.action_class_map.get(task.action, None)(
                    task,
                    self.orchestrator,
                    self.state_manager,
                    maas_client=maas_client)
                action.start()
            except Exception as e:
                msg = "Subtask for action %s raised unexpected exceptions" % task.action
                self.logger.error(
                    msg, exc_info=e.exception())
                task.add_status_msg(
                    msg,
                    error=True,
                    ctx=str(task.get_id()),
                    ctx_type='task')
                task.failure()

        task.set_status(hd_fields.TaskStatus.Complete)
        task.save()

        return

    def get_available_images(self):
        """Return images available in MAAS."""
        maas_client = MaasRequestFactory(
            config.config_mgr.conf.maasdriver.maas_api_url,
            config.config_mgr.conf.maasdriver.maas_api_key)

        br = BootResources(maas_client)
        br.refresh()

        return br.get_available_images()

    def get_available_kernels(self, image_name):
        """Return kernels available for ``image_name``.

        :param image_name: str image name (e.g. 'xenial')
        """
        maas_client = MaasRequestFactory(
            config.config_mgr.conf.maasdriver.maas_api_url,
            config.config_mgr.conf.maasdriver.maas_api_key)

        br = BootResources(maas_client)
        br.refresh()

        return br.get_available_kernels(image_name)


def list_opts():
    return {MaasNodeDriver.driver_key: MaasNodeDriver.maasdriver_options}

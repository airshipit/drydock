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
import time
import logging
import traceback
import sys
import uuid

from oslo_config import cfg

import drydock_provisioner.error as errors
import drydock_provisioner.drivers as drivers
import drydock_provisioner.objects.fields as hd_fields
import drydock_provisioner.objects.task as task_model

from drydock_provisioner.drivers.node import NodeDriver
from .api_client import MaasRequestFactory

import drydock_provisioner.drivers.node.maasdriver.models.fabric as maas_fabric
import drydock_provisioner.drivers.node.maasdriver.models.vlan as maas_vlan
import drydock_provisioner.drivers.node.maasdriver.models.subnet as maas_subnet
import drydock_provisioner.drivers.node.maasdriver.models.machine as maas_machine
import drydock_provisioner.drivers.node.maasdriver.models.tag as maas_tag
import drydock_provisioner.drivers.node.maasdriver.models.sshkey as maas_keys

class MaasNodeDriver(NodeDriver):
    maasdriver_options = [
        cfg.StrOpt('maas_api_key', help='The API key for accessing MaaS', secret=True),
        cfg.StrOpt('maas_api_url', help='The URL for accessing MaaS API'),
        cfg.IntOpt('poll_interval', default=10, help='Polling interval for querying MaaS status in seconds'),
    ]

    driver_name = 'maasdriver'
    driver_key = 'maasdriver'
    driver_desc = 'MaaS Node Provisioning Driver'

    def __init__(self, **kwargs):
        super(MaasNodeDriver, self).__init__(**kwargs)
	
        cfg.CONF.register_opts(MaasNodeDriver.maasdriver_options, group=MaasNodeDriver.driver_key)

        self.logger = logging.getLogger(cfg.CONF.logging.nodedriver_logger_name)

    def execute_task(self, task_id):
        task = self.state_manager.get_task(task_id)

        if task is None:
            raise errors.DriverError("Invalid task %s" % (task_id))

        if task.action not in self.supported_actions:
            raise errors.DriverError("Driver %s doesn't support task action %s"
                % (self.driver_desc, task.action))

        if task.action == hd_fields.OrchestratorAction.ValidateNodeServices:
            self.orchestrator.task_field_update(task.get_id(),
                                status=hd_fields.TaskStatus.Running)
            maas_client = MaasRequestFactory(cfg.CONF.maasdriver.maas_api_url, cfg.CONF.maasdriver.maas_api_key) 

            try:
                if maas_client.test_connectivity():
                    if maas_client.test_authentication():
                        self.orchestrator.task_field_update(task.get_id(),
                            status=hd_fields.TaskStatus.Complete,
                            result=hd_fields.ActionResult.Success)
                        return
            except errors.TransientDriverError(ex):
                result = {
                    'retry': True,
                    'detail':  str(ex),
                }
                self.orchestrator.task_field_update(task.get_id(),
                            status=hd_fields.TaskStatus.Complete,
                            result=hd_fields.ActionResult.Failure,
                            result_details=result)
                return
            except errors.PersistentDriverError(ex):
                result = {
                    'retry': False,
                    'detail':  str(ex),
                }
                self.orchestrator.task_field_update(task.get_id(),
                            status=hd_fields.TaskStatus.Complete,
                            result=hd_fields.ActionResult.Failure,
                            result_details=result)
                return
            except Exception(ex):
                result = {
                    'retry': False,
                    'detail':  str(ex),
                }
                self.orchestrator.task_field_update(task.get_id(),
                            status=hd_fields.TaskStatus.Complete,
                            result=hd_fields.ActionResult.Failure,
                            result_details=result)
                return

        design_id = getattr(task, 'design_id', None)

        if design_id is None:
            raise errors.DriverError("No design ID specified in task %s" %
                                     (task_id))


        if task.site_name is None:
            raise errors.DriverError("No site specified for task %s." %
                                    (task_id))

        self.orchestrator.task_field_update(task.get_id(),
                            status=hd_fields.TaskStatus.Running)

        site_design = self.orchestrator.get_effective_site(design_id)

        if task.action == hd_fields.OrchestratorAction.CreateNetworkTemplate:
            self.orchestrator.task_field_update(task.get_id(), status=hd_fields.TaskStatus.Running)

            subtask = self.orchestrator.create_task(task_model.DriverTask,
                        parent_task_id=task.get_id(), design_id=design_id,
                        action=task.action, site_name=task.site_name,
                        task_scope={'site': task.site_name})
            runner = MaasTaskRunner(state_manager=self.state_manager,
                        orchestrator=self.orchestrator,
                        task_id=subtask.get_id())

            self.logger.info("Starting thread for task %s to create network templates" % (subtask.get_id()))

            runner.start()

            runner.join(timeout=cfg.CONF.timeouts.create_network_template * 60)

            if runner.is_alive():
                result =  {
                    'retry': False,
                    'detail': 'MaaS Network creation timed-out'
                }
                self.logger.warning("Thread for task %s timed out after 120s" % (subtask.get_id()))
                self.orchestrator.task_field_update(task.get_id(),
                            status=hd_fields.TaskStatus.Complete,
                            result=hd_fields.ActionResult.Failure,
                            result_detail=result)
            else:
                subtask = self.state_manager.get_task(subtask.get_id())
                self.logger.info("Thread for task %s completed - result %s" % (subtask.get_id(), subtask.get_result()))
                self.orchestrator.task_field_update(task.get_id(),
                            status=hd_fields.TaskStatus.Complete,
                            result=subtask.get_result())

            return
        elif task.action == hd_fields.OrchestratorAction.ConfigureUserCredentials:
            self.orchestrator.task_field_update(task.get_id(), status=hd_fields.TaskStatus.Running)

            subtask = self.orchestrator.create_task(task_model.DriverTask,
                        parent_task_id=task.get_id(), design_id=design_id,
                        action=task.action, site_name=task.site_name,
                        task_scope={'site': task.site_name})
            runner = MaasTaskRunner(state_manager=self.state_manager,
                        orchestrator=self.orchestrator,
                        task_id=subtask.get_id())

            self.logger.info("Starting thread for task %s to configure user credentials" % (subtask.get_id()))

            runner.start()

            runner.join(timeout=cfg.CONF.timeouts.configure_user_credentials * 60)

            if runner.is_alive():
                result =  {
                    'retry': False,
                    'detail': 'MaaS ssh key creation timed-out'
                }
                self.logger.warning("Thread for task %s timed out after 120s" % (subtask.get_id()))
                self.orchestrator.task_field_update(task.get_id(),
                            status=hd_fields.TaskStatus.Complete,
                            result=hd_fields.ActionResult.Failure,
                            result_detail=result)
            else:
                subtask = self.state_manager.get_task(subtask.get_id())
                self.logger.info("Thread for task %s completed - result %s" % (subtask.get_id(), subtask.get_result()))
                self.orchestrator.task_field_update(task.get_id(),
                            status=hd_fields.TaskStatus.Complete,
                            result=subtask.get_result())

            return
        elif task.action == hd_fields.OrchestratorAction.IdentifyNode:
            self.orchestrator.task_field_update(task.get_id(),
                                status=hd_fields.TaskStatus.Running)

            subtasks = []

            result_detail = {
                'detail': [],
                'failed_nodes': [],
                'successful_nodes': [],
            }

            for n in task.node_list:
                subtask = self.orchestrator.create_task(task_model.DriverTask,
                        parent_task_id=task.get_id(), design_id=design_id,
                        action=hd_fields.OrchestratorAction.IdentifyNode,
                        site_name=task.site_name,
                        task_scope={'site': task.site_name, 'node_names': [n]})
                runner = MaasTaskRunner(state_manager=self.state_manager,
                        orchestrator=self.orchestrator,
                        task_id=subtask.get_id())

                self.logger.info("Starting thread for task %s to identify node %s" % (subtask.get_id(), n))

                runner.start()
                subtasks.append(subtask.get_id())

            cleaned_subtasks = []
            attempts = 0
            max_attempts = cfg.CONF.timeouts.identify_node * (60 // cfg.CONF.poll_interval)
            worked = failed = False

            self.logger.debug("Polling for subtask completetion every %d seconds, a max of %d polls." %
                                (cfg.CONF.poll_interval, max_attempts))
            while len(cleaned_subtasks) < len(subtasks) and attempts < max_attempts:
                for t in subtasks:
                    if t in cleaned_subtasks:
                        continue

                    subtask = self.state_manager.get_task(t)

                    if subtask.status == hd_fields.TaskStatus.Complete:
                        self.logger.info("Task %s to identify node complete - status %s" %
                                        (subtask.get_id(), subtask.get_result()))
                        cleaned_subtasks.append(t)

                        if subtask.result == hd_fields.ActionResult.Success:
                            result_detail['successful_nodes'].extend(subtask.node_list)
                            worked = True
                        elif subtask.result == hd_fields.ActionResult.Failure:
                            result_detail['failed_nodes'].extend(subtask.node_list)
                            failed = True
                        elif subtask.result == hd_fields.ActionResult.PartialSuccess:
                            worked = failed = True

                time.sleep(cfg.CONF.maasdriver.poll_interval)
                attempts = attempts + 1

            if len(cleaned_subtasks) < len(subtasks):
                self.logger.warning("Time out for task %s before all subtask threads complete" % (task.get_id()))
                result = hd_fields.ActionResult.DependentFailure
                result_detail['detail'].append('Some subtasks did not complete before the timeout threshold')
            elif worked and failed:
                result = hd_fields.ActionResult.PartialSuccess
            elif worked:
                result = hd_fields.ActionResult.Success
            else:
                result = hd_fields.ActionResult.Failure

            self.orchestrator.task_field_update(task.get_id(),
                                status=hd_fields.TaskStatus.Complete,
                                result=result,
                                result_detail=result_detail)
        elif task.action == hd_fields.OrchestratorAction.ConfigureHardware:
            self.orchestrator.task_field_update(task.get_id(),
                                status=hd_fields.TaskStatus.Running)

            self.logger.debug("Starting subtask to commissiong %s nodes." % (len(task.node_list)))

            subtasks = []

            result_detail = {
                'detail': [],
                'failed_nodes': [],
                'successful_nodes': [],
            }

            for n in task.node_list:
                subtask = self.orchestrator.create_task(task_model.DriverTask,
                        parent_task_id=task.get_id(), design_id=design_id,
                        action=hd_fields.OrchestratorAction.ConfigureHardware,
                        site_name=task.site_name,
                        task_scope={'site': task.site_name, 'node_names': [n]})
                runner = MaasTaskRunner(state_manager=self.state_manager,
                        orchestrator=self.orchestrator,
                        task_id=subtask.get_id())

                self.logger.info("Starting thread for task %s to commission node %s" % (subtask.get_id(), n))

                runner.start()
                subtasks.append(subtask.get_id())

            cleaned_subtasks = []
            attempts = 0
            max_attempts = cfg.CONF.timeouts.configure_hardware * (60 // cfg.CONF.poll_interval)
            worked = failed = False

            self.logger.debug("Polling for subtask completetion every %d seconds, a max of %d polls." %
                                (cfg.CONF.poll_interval, max_attempts))
            while len(cleaned_subtasks) < len(subtasks) and attempts < max_attempts:
                for t in subtasks:
                    if t in cleaned_subtasks:
                        continue

                    subtask = self.state_manager.get_task(t)

                    if subtask.status == hd_fields.TaskStatus.Complete:
                        self.logger.info("Task %s to commission node complete - status %s" %
                                        (subtask.get_id(), subtask.get_result()))
                        cleaned_subtasks.append(t)

                        if subtask.result == hd_fields.ActionResult.Success:
                            result_detail['successful_nodes'].extend(subtask.node_list)
                            worked = True
                        elif subtask.result == hd_fields.ActionResult.Failure:
                            result_detail['failed_nodes'].extend(subtask.node_list)
                            failed = True
                        elif subtask.result == hd_fields.ActionResult.PartialSuccess:
                            worked = failed = True

                time.sleep(cfg.CONF.maasdriver.poll_interval)
                attempts = attempts + 1

            if len(cleaned_subtasks) < len(subtasks):
                self.logger.warning("Time out for task %s before all subtask threads complete" % (task.get_id()))
                result = hd_fields.ActionResult.DependentFailure
                result_detail['detail'].append('Some subtasks did not complete before the timeout threshold')
            elif worked and failed:
                result = hd_fields.ActionResult.PartialSuccess
            elif worked:
                result = hd_fields.ActionResult.Success
            else:
                result = hd_fields.ActionResult.Failure

            self.orchestrator.task_field_update(task.get_id(),
                                status=hd_fields.TaskStatus.Complete,
                                result=result,
                                result_detail=result_detail)
        elif task.action == hd_fields.OrchestratorAction.ApplyNodeNetworking:
            self.orchestrator.task_field_update(task.get_id(),
                                status=hd_fields.TaskStatus.Running)

            self.logger.debug("Starting subtask to configure networking on %s nodes." % (len(task.node_list)))

            subtasks = []

            result_detail = {
                'detail': [],
                'failed_nodes': [],
                'successful_nodes': [],
            }

            for n in task.node_list:
                subtask = self.orchestrator.create_task(task_model.DriverTask,
                        parent_task_id=task.get_id(), design_id=design_id,
                        action=hd_fields.OrchestratorAction.ApplyNodeNetworking,
                        site_name=task.site_name,
                        task_scope={'site': task.site_name, 'node_names': [n]})
                runner = MaasTaskRunner(state_manager=self.state_manager,
                        orchestrator=self.orchestrator,
                        task_id=subtask.get_id())

                self.logger.info("Starting thread for task %s to configure networking on node %s" % (subtask.get_id(), n))

                runner.start()
                subtasks.append(subtask.get_id())

            cleaned_subtasks = []
            attempts = 0
            max_attempts = cfg.CONF.timeouts.apply_node_networking * (60 // cfg.CONF.poll_interval)
            worked = failed = False

            self.logger.debug("Polling for subtask completetion every %d seconds, a max of %d polls." %
                                (cfg.CONF.poll_interval, max_attempts))
            while len(cleaned_subtasks) < len(subtasks) and attempts < max_attempts:
                for t in subtasks:
                    if t in cleaned_subtasks:
                        continue

                    subtask = self.state_manager.get_task(t)

                    if subtask.status == hd_fields.TaskStatus.Complete:
                        self.logger.info("Task %s to apply networking complete - status %s" %
                                        (subtask.get_id(), subtask.get_result()))
                        cleaned_subtasks.append(t)

                        if subtask.result == hd_fields.ActionResult.Success:
                            result_detail['successful_nodes'].extend(subtask.node_list)
                            worked = True
                        elif subtask.result == hd_fields.ActionResult.Failure:
                            result_detail['failed_nodes'].extend(subtask.node_list)
                            failed = True
                        elif subtask.result == hd_fields.ActionResult.PartialSuccess:
                            worked = failed = True

                time.sleep(cfg.CONF.poll_interval)
                attempts = attempts + 1

            if len(cleaned_subtasks) < len(subtasks):
                self.logger.warning("Time out for task %s before all subtask threads complete" % (task.get_id()))
                result = hd_fields.ActionResult.DependentFailure
                result_detail['detail'].append('Some subtasks did not complete before the timeout threshold')
            elif worked and failed:
                result = hd_fields.ActionResult.PartialSuccess
            elif worked:
                result = hd_fields.ActionResult.Success
            else:
                result = hd_fields.ActionResult.Failure

            self.orchestrator.task_field_update(task.get_id(),
                                status=hd_fields.TaskStatus.Complete,
                                result=result,
                                result_detail=result_detail)
        elif task.action == hd_fields.OrchestratorAction.ApplyNodePlatform:
            self.orchestrator.task_field_update(task.get_id(),
                                status=hd_fields.TaskStatus.Running)

            self.logger.debug("Starting subtask to configure the platform on %s nodes." % (len(task.node_list)))

            subtasks = []

            result_detail = {
                'detail': [],
                'failed_nodes': [],
                'successful_nodes': [],
            }

            for n in task.node_list:
                subtask = self.orchestrator.create_task(task_model.DriverTask,
                        parent_task_id=task.get_id(), design_id=design_id,
                        action=hd_fields.OrchestratorAction.ApplyNodePlatform,
                        site_name=task.site_name,
                        task_scope={'site': task.site_name, 'node_names': [n]})
                runner = MaasTaskRunner(state_manager=self.state_manager,
                        orchestrator=self.orchestrator,
                        task_id=subtask.get_id())

                self.logger.info("Starting thread for task %s to config node %s platform" % (subtask.get_id(), n))

                runner.start()
                subtasks.append(subtask.get_id())

            cleaned_subtasks = []
            attempts = 0
            max_attempts = cfg.CONF.timeouts.apply_node_platform * (60 // cfg.CONF.poll_interval)
            worked = failed = False

            self.logger.debug("Polling for subtask completetion every %d seconds, a max of %d polls." %
                                (cfg.CONF.poll_interval, max_attempts))

            while len(cleaned_subtasks) < len(subtasks) and attempts < max_attempts:
                for t in subtasks:
                    if t in cleaned_subtasks:
                        continue

                    subtask = self.state_manager.get_task(t)

                    if subtask.status == hd_fields.TaskStatus.Complete:
                        self.logger.info("Task %s to configure node platform complete - status %s" %
                                        (subtask.get_id(), subtask.get_result()))
                        cleaned_subtasks.append(t)

                        if subtask.result == hd_fields.ActionResult.Success:
                            result_detail['successful_nodes'].extend(subtask.node_list)
                            worked = True
                        elif subtask.result == hd_fields.ActionResult.Failure:
                            result_detail['failed_nodes'].extend(subtask.node_list)
                            failed = True
                        elif subtask.result == hd_fields.ActionResult.PartialSuccess:
                            worked = failed = True

                time.sleep(cfg.CONF.poll_interval)
                attempts = attempts + 1

            if len(cleaned_subtasks) < len(subtasks):
                self.logger.warning("Time out for task %s before all subtask threads complete" % (task.get_id()))
                result = hd_fields.ActionResult.DependentFailure
                result_detail['detail'].append('Some subtasks did not complete before the timeout threshold')
            elif worked and failed:
                result = hd_fields.ActionResult.PartialSuccess
            elif worked:
                result = hd_fields.ActionResult.Success
            else:
                result = hd_fields.ActionResult.Failure

            self.orchestrator.task_field_update(task.get_id(),
                                status=hd_fields.TaskStatus.Complete,
                                result=result,
                                result_detail=result_detail)
        elif task.action == hd_fields.OrchestratorAction.DeployNode:
            self.orchestrator.task_field_update(task.get_id(),
                                status=hd_fields.TaskStatus.Running)

            self.logger.debug("Starting subtask to deploy %s nodes." % (len(task.node_list)))

            subtasks = []

            result_detail = {
                'detail': [],
                'failed_nodes': [],
                'successful_nodes': [],
            }

            for n in task.node_list:
                subtask = self.orchestrator.create_task(task_model.DriverTask,
                        parent_task_id=task.get_id(), design_id=design_id,
                        action=hd_fields.OrchestratorAction.DeployNode,
                        site_name=task.site_name,
                        task_scope={'site': task.site_name, 'node_names': [n]})
                runner = MaasTaskRunner(state_manager=self.state_manager,
                        orchestrator=self.orchestrator,
                        task_id=subtask.get_id())

                self.logger.info("Starting thread for task %s to deploy node %s" % (subtask.get_id(), n))

                runner.start()
                subtasks.append(subtask.get_id())

            cleaned_subtasks = []
            attempts = 0
            max_attempts = cfg.CONF.timeouts.deploy_node * (60 // cfg.CONF.poll_interval)
            worked = failed = False

            self.logger.debug("Polling for subtask completetion every %d seconds, a max of %d polls." %
                                (cfg.CONF.poll_interval, max_attempts))

            while len(cleaned_subtasks) < len(subtasks) and attempts < max_attempts:
                for t in subtasks:
                    if t in cleaned_subtasks:
                        continue

                    subtask = self.state_manager.get_task(t)

                    if subtask.status == hd_fields.TaskStatus.Complete:
                        self.logger.info("Task %s to deploy node complete - status %s" %
                                        (subtask.get_id(), subtask.get_result()))
                        cleaned_subtasks.append(t)

                        if subtask.result == hd_fields.ActionResult.Success:
                            result_detail['successful_nodes'].extend(subtask.node_list)
                            worked = True
                        elif subtask.result == hd_fields.ActionResult.Failure:
                            result_detail['failed_nodes'].extend(subtask.node_list)
                            failed = True
                        elif subtask.result == hd_fields.ActionResult.PartialSuccess:
                            worked = failed = True

                time.sleep(max_attempts)
                attempts = attempts + 1

            if len(cleaned_subtasks) < len(subtasks):
                self.logger.warning("Time out for task %s before all subtask threads complete" % (task.get_id()))
                result = hd_fields.ActionResult.DependentFailure
                result_detail['detail'].append('Some subtasks did not complete before the timeout threshold')
            elif worked and failed:
                result = hd_fields.ActionResult.PartialSuccess
            elif worked:
                result = hd_fields.ActionResult.Success
            else:
                result = hd_fields.ActionResult.Failure

            self.orchestrator.task_field_update(task.get_id(),
                                status=hd_fields.TaskStatus.Complete,
                                result=result,
                                result_detail=result_detail)

class MaasTaskRunner(drivers.DriverTaskRunner):

    def __init__(self, **kwargs):
        super(MaasTaskRunner, self).__init__(**kwargs)

        # TODO Need to build this name from configs
        self.logger = logging.getLogger('drydock.nodedriver.maasdriver')

    def execute_task(self):
        task_action = self.task.action

        self.orchestrator.task_field_update(self.task.get_id(),
                            status=hd_fields.TaskStatus.Running,
                            result=hd_fields.ActionResult.Incomplete)

        self.maas_client = MaasRequestFactory(cfg.CONF.maasdriver.maas_api_url,
                                              cfg.CONF.maasdriver.maas_api_key)

        site_design = self.orchestrator.get_effective_site(self.task.design_id)

        if task_action == hd_fields.OrchestratorAction.CreateNetworkTemplate:
            # Try to true up MaaS definitions of fabrics/vlans/subnets
            # with the networks defined in Drydock
            design_networks = site_design.networks
            design_links = site_design.network_links

            fabrics = maas_fabric.Fabrics(self.maas_client)
            fabrics.refresh()

            subnets = maas_subnet.Subnets(self.maas_client)
            subnets.refresh()

            result_detail = {
                'detail': []
            }

            for l in design_links:
                if l.metalabels is not None:
                    # TODO move metalabels into config
                    if 'noconfig' in l.metalabels:
                        self.logger.info("NetworkLink %s marked 'noconfig', skipping configuration including allowed networks." % (l.name))
                        continue

                fabrics_found = set()

                # First loop through the possible Networks on this NetworkLink
                # and validate that MaaS's self-discovered networking matches
                # our design. This means all self-discovered networks that are matched
                # to a link need to all be part of the same fabric. Otherwise there is no
                # way to reconcile the discovered topology with the designed topology
                for net_name in l.allowed_networks:
                    n = site_design.get_network(net_name)

                    if n is None:
                        self.logger.warning("Network %s allowed on link %s, but not defined." % (net_name, l.name))
                        continue

                    maas_net = subnets.singleton({'cidr': n.cidr})

                    if maas_net is not None:
                        fabrics_found.add(maas_net.fabric)

                if len(fabrics_found) > 1:
                    self.logger.warning("MaaS self-discovered network incompatible with NetworkLink %s" % l.name)
                    continue
                elif len(fabrics_found) == 1:
                    link_fabric_id = fabrics_found.pop()
                    link_fabric = fabrics.select(link_fabric_id)
                    link_fabric.name = l.name
                    link_fabric.update()
                else:
                    link_fabric = fabrics.singleton({'name': l.name})

                    if link_fabric is None:
                        link_fabric = maas_fabric.Fabric(self.maas_client, name=l.name)
                        fabrics.add(link_fabric)


                # Now that we have the fabrics sorted out, check
                # that VLAN tags and subnet attributes are correct
                for net_name in l.allowed_networks:
                    n = site_design.get_network(net_name)

                    if n is None:
                        continue

                    try:
                        subnet = subnets.singleton({'cidr': n.cidr})

                        if subnet is None:
                            self.logger.info("Subnet for network %s not found, creating..." % (n.name))

                            fabric_list = maas_fabric.Fabrics(self.maas_client)
                            fabric_list.refresh()
                            fabric = fabric_list.singleton({'name': l.name})
                        
                            if fabric is not None:
                                vlan_list = maas_vlan.Vlans(self.maas_client, fabric_id=fabric.resource_id)
                                vlan_list.refresh()
                            
                                vlan = vlan_list.singleton({'vid': n.vlan_id if n.vlan_id is not None else 0})

                                if vlan is not None:
                                    vlan.name = n.name

                                    if getattr(n, 'mtu', None) is not None:
                                        vlan.mtu = n.mtu

                                    vlan.update()
                                    result_detail['detail'].append("VLAN %s found for network %s, updated attributes"
                                                    % (vlan.resource_id, n.name))
                                else:
                                    # Create a new VLAN in this fabric and assign subnet to it
                                    vlan = maas_vlan.Vlan(self.maas_client, name=n.name, vid=n.vlan_id,
                                                        mtu=getattr(n, 'mtu', None),fabric_id=fabric.resource_id)
                                    vlan = vlan_list.add(vlan)

                                    result_detail['detail'].append("VLAN %s created for network %s"
                                                                    % (vlan.resource_id, n.name))
                    
                                # If subnet did not exist, create it here and attach it to the fabric/VLAN
                                subnet = maas_subnet.Subnet(self.maas_client, name=n.name, cidr=n.cidr, fabric=fabric.resource_id,
                                                            vlan=vlan.resource_id, gateway_ip=n.get_default_gateway())

                                subnet_list = maas_subnet.Subnets(self.maas_client)
                                subnet = subnet_list.add(subnet)
                                self.logger.info("Created subnet %s for CIDR %s on VLAN %s" %
                                                (subnet.resource_id, subnet.cidr, subnet.vlan))

                                result_detail['detail'].append("Subnet %s created for network %s" % (subnet.resource_id, n.name))
                            else:
                                self.logger.error("Fabric %s should be created, but cannot locate it." % (l.name))
                        else:
                            subnet.name = n.name
                            subnet.dns_servers = n.dns_servers

                            result_detail['detail'].append("Subnet %s found for network %s, updated attributes"
                                                    % (subnet.resource_id, n.name))
                            self.logger.info("Updating existing MaaS subnet %s" % (subnet.resource_id))

                            vlan_list = maas_vlan.Vlans(self.maas_client, fabric_id=subnet.fabric)
                            vlan_list.refresh()

                            vlan = vlan_list.select(subnet.vlan)

                            if vlan is not None:
                                vlan.name = n.name
                                vlan.set_vid(n.vlan_id)

                                if getattr(n, 'mtu', None) is not None:
                                    vlan.mtu = n.mtu

                                vlan.update()
                                result_detail['detail'].append("VLAN %s found for network %s, updated attributes"
                                                                        % (vlan.resource_id, n.name))
                            else:
                                self.logger.error("MaaS subnet %s does not have a matching VLAN" % (subnet.resource_id))
                                continue
                
                        # Check if the routes have a default route
                        subnet.gateway_ip = n.get_default_gateway()
                        subnet.update()

                        dhcp_on = False

                        for r in n.ranges:
                            subnet.add_address_range(r)
                            if r.get('type', None) == 'dhcp':
                                dhcp_on = True

                        vlan_list = maas_vlan.Vlans(self.maas_client, fabric_id=subnet.fabric)
                        vlan_list.refresh()
                        vlan = vlan_list.select(subnet.vlan)

                        if dhcp_on and not vlan.dhcp_on:
                            self.logger.info("DHCP enabled for subnet %s, activating in MaaS" % (subnet.name))


                            # TODO Ugly hack assuming a single rack controller for now until we implement multirack
                            resp = self.maas_client.get("rackcontrollers/")

                            if resp.ok:
                                resp_json = resp.json()

                                if not isinstance(resp_json, list):
                                    self.logger.warning("Unexpected response when querying list of rack controllers")
                                    self.logger.debug("%s" % resp.text)
                                else:
                                    if len(resp_json) > 1:
                                        self.logger.warning("Received more than one rack controller, defaulting to first")

                                    rackctl_id = resp_json[0]['system_id']

                                    vlan.dhcp_on = True
                                    vlan.primary_rack = rackctl_id
                                    vlan.update()
                                    self.logger.debug("Enabling DHCP on VLAN %s managed by rack ctlr %s" %
                                                      (vlan.resource_id, rackctl_id))
                        elif dhcp_on and vlan.dhcp_on:
                            self.logger.info("DHCP already enabled for subnet %s" % (subnet.resource_id))


                        # TODO sort out static route support as MaaS seems to require the destination
                        # network be defined in MaaS as well

                    except ValueError as vex:
                        raise errors.DriverError("Inconsistent data from MaaS")
                    
            subnet_list = maas_subnet.Subnets(self.maas_client)
            subnet_list.refresh()

            action_result = hd_fields.ActionResult.Incomplete

            success_rate = 0

            for n in design_networks:
                if n.metalabels is not None:
                    # TODO move metalabels into config
                    if 'noconfig' in n.metalabels:
                        self.logger.info("Network %s marked 'noconfig', skipping validation." % (l.name))
                        continue

                exists = subnet_list.query({'cidr': n.cidr})
                if len(exists) > 0:
                    subnet = exists[0]
                    if subnet.name == n.name:
                        success_rate = success_rate + 1
                    else:
                        success_rate = success_rate + 1
                else:
                    success_rate = success_rate + 1

            if success_rate == len(design_networks):
                action_result = hd_fields.ActionResult.Success
            elif success_rate == - (len(design_networks)):
                action_result = hd_fields.ActionResult.Failure
            else:
                action_result = hd_fields.ActionResult.PartialSuccess

            self.orchestrator.task_field_update(self.task.get_id(),
                            status=hd_fields.TaskStatus.Complete,
                            result=action_result,
                            result_detail=result_detail)
        elif task_action == hd_fields.OrchestratorAction.ConfigureUserCredentials:
            try:
                key_list = maas_keys.SshKeys(self.maas_client)
                key_list.refresh()
            except:
                self.orchestrator.task_field_update(self.task.get_id(),
                            status=hd_fields.TaskStatus.Complete,
                            result=hd_fields.ActionResult.Failure,
                            result_detail={'detail': 'Error accessing MaaS SshKeys API', 'retry': True})
                return

            site_model = site_design.get_site()

            result_detail = { 'detail': [] }
            failed = worked = False
            for k in getattr(site_model, 'authorized_keys', []):
                try:
                    if len(key_list.query({'key': k.replace("\n","")})) == 0:
                        new_key = maas_keys.SshKey(self.maas_client, key=k)
                        new_key = key_list.add(new_key)
                        self.logger.debug("Added SSH key %s to MaaS user profile. Will be installed on all deployed nodes." %
                                    (k[:16]))
                        result_detail['detail'].append("Added SSH key %s" % (k[:16]))
                        worked = True
                    else:
                        self.logger.debug("SSH key %s already exists in MaaS user profile." % k[:16])
                        result_detail['detail'].append("SSH key %s alreayd exists" % (k[:16]))
                        worked = True
                except Exception as ex:
                    self.logger.warning("Error adding SSH key to MaaS user profile: %s" % str(ex))
                    result_detail['detail'].append("Failed to add SSH key %s" % (k[:16]))
                    failed = True

            if worked and failed:
                final_result = hd_fields.ActionResult.PartialSuccess
            elif worked:
                final_result = hd_fields.ActionResult.Success
            else:
                final_result = hd_fields.ActionResult.Failure

            self.orchestrator.task_field_update(self.task.get_id(),
                            status=hd_fields.TaskStatus.Complete,
                            result=final_result, result_detail=result_detail)
            return
        elif task_action == hd_fields.OrchestratorAction.IdentifyNode:
            try:
                machine_list = maas_machine.Machines(self.maas_client)
                machine_list.refresh()
            except:
                self.orchestrator.task_field_update(self.task.get_id(),
                            status=hd_fields.TaskStatus.Complete,
                            result=hd_fields.ActionResult.Failure,
                            result_detail={'detail': 'Error accessing MaaS Machines API', 'retry': True})
                return

            nodes = self.task.node_list

            result_detail = {'detail': []}

            worked = failed = False

            for n in nodes:
                try:
                    node = site_design.get_baremetal_node(n)
                    machine = machine_list.identify_baremetal_node(node)
                    if machine is not None:
                        worked = True
                        result_detail['detail'].append("Node %s identified in MaaS" % n)
                    else:
                        failed = True
                        result_detail['detail'].append("Node %s not found in MaaS" % n)
                except Exception as ex:
                    failed = True
                    result_detail['detail'].append("Error identifying node %s: %s" % (n, str(ex)))

            result = None
            if worked and failed:
                result = hd_fields.ActionResult.PartialSuccess
            elif worked:
                result = hd_fields.ActionResult.Success
            elif failed:
                result = hd_fields.ActionResult.Failure

            self.orchestrator.task_field_update(self.task.get_id(),
                                                status=hd_fields.TaskStatus.Complete,
                                                result=result,
                                                result_detail=result_detail)
        elif task_action == hd_fields.OrchestratorAction.ConfigureHardware:
            try:
                machine_list = maas_machine.Machines(self.maas_client)
                machine_list.refresh()
            except:
                self.orchestrator.task_field_update(self.task.get_id(),
                            status=hd_fields.TaskStatus.Complete,
                            result=hd_fields.ActionResult.Failure,
                            result_detail={'detail': 'Error accessing MaaS Machines API', 'retry': True})
                return

            nodes = self.task.node_list

            result_detail = {'detail': []}

            worked = failed = False

            # TODO Better way of representing the node statuses than static strings
            for n in nodes:
                try:
                    self.logger.debug("Locating node %s for commissioning" % (n))
                    node = site_design.get_baremetal_node(n)
                    machine = machine_list.identify_baremetal_node(node, update_name=False)
                    if machine is not None:
                        if machine.status_name in ['New', 'Broken']:
                            self.logger.debug("Located node %s in MaaS, starting commissioning" % (n))
                            machine.commission()

                            # Poll machine status
                            attempts = 0
                            max_attempts = cfg.CONF.timeouts.configure_hardware * (60 // cfg.CONF.maasdriver.poll_interval)

                            while (attempts < max_attempts and 
                                      (machine.status_name != 'Ready' and not machine.status_name.startswith('Failed'))):
                                attempts = attempts + 1
                                time.sleep(cfg.CONF.maasdriver.poll_interval)
                                try:
                                    machine.refresh()
                                    self.logger.debug("Polling node %s status attempt %d of %d: %s" % (n, attempts, max_attempts, machine.status_name))
                                except:
                                    self.logger.warning("Error updating node %s status during commissioning, will re-attempt." %
                                                     (n))
                            if machine.status_name == 'Ready':
                                self.logger.info("Node %s commissioned." % (n))
                                result_detail['detail'].append("Node %s commissioned" % (n))
                                worked = True
                        elif machine.status_name == 'Commissioning':
                            self.logger.info("Located node %s in MaaS, node already being commissioned. Skipping..." % (n))
                            result_detail['detail'].append("Located node %s in MaaS, node already being commissioned. Skipping..." % (n))
                            worked = True
                        elif machine.status_name == 'Ready':
                            self.logger.info("Located node %s in MaaS, node commissioned. Skipping..." % (n))
                            result_detail['detail'].append("Located node %s in MaaS, node commissioned. Skipping..." % (n))
                            worked = True
                        else:
                            self.logger.warning("Located node %s in MaaS, unknown status %s. Skipping..." % (n, machine.status_name))
                            result_detail['detail'].append("Located node %s in MaaS, node commissioned. Skipping..." % (n))
                            failed = True
                    else:
                        self.logger.warning("Node %s not found in MaaS" % n)
                        failed = True
                        result_detail['detail'].append("Node %s not found in MaaS" % n)

                except Exception as ex:
                    failed = True
                    result_detail['detail'].append("Error commissioning node %s: %s" % (n, str(ex)))

            result = None
            if worked and failed:
                result = hd_fields.ActionResult.PartialSuccess
            elif worked:
                result = hd_fields.ActionResult.Success
            elif failed:
                result = hd_fields.ActionResult.Failure

            self.orchestrator.task_field_update(self.task.get_id(),
                                                status=hd_fields.TaskStatus.Complete,
                                                result=result,
                                                result_detail=result_detail)
        elif task_action == hd_fields.OrchestratorAction.ApplyNodeNetworking:
            try:
                machine_list = maas_machine.Machines(self.maas_client)
                machine_list.refresh()
 
                fabrics = maas_fabric.Fabrics(self.maas_client)
                fabrics.refresh()

                subnets = maas_subnet.Subnets(self.maas_client)
                subnets.refresh()
            except Exception as ex:
                self.logger.error("Error applying node networking, cannot access MaaS: %s" % str(ex))
                traceback.print_tb(sys.last_traceback)
                self.orchestrator.task_field_update(self.task.get_id(),
                            status=hd_fields.TaskStatus.Complete,
                            result=hd_fields.ActionResult.Failure,
                            result_detail={'detail': 'Error accessing MaaS API', 'retry': True})
                return

            nodes = self.task.node_list

            result_detail = {'detail': []}

            worked = failed = False

            # TODO Better way of representing the node statuses than static strings
            for n in nodes:
                try:
                    self.logger.debug("Locating node %s for network configuration" % (n))

                    node = site_design.get_baremetal_node(n)
                    machine = machine_list.identify_baremetal_node(node, update_name=False)

                    if machine is not None:
                        if machine.status_name == 'Ready':
                            self.logger.debug("Located node %s in MaaS, starting interface configuration" % (n))
                            
                            for i in node.interfaces:
                                nl = site_design.get_network_link(i.network_link)

                                if nl.metalabels is not None:
                                    if 'noconfig' in nl.metalabels:
                                        self.logger.info("Interface %s connected to NetworkLink %s marked 'noconfig', skipping." %
                                                        (i.device_name, nl.name))
                                        continue

                                fabric = fabrics.singleton({'name': nl.name})

                                if fabric is None:
                                    self.logger.error("No fabric found for NetworkLink %s" % (nl.name))
                                    failed = True
                                    continue

                                # TODO HardwareProfile device alias integration
                                iface = machine.get_network_interface(i.device_name)

                                if iface is None:
                                    self.logger.warning("Interface %s not found on node %s, skipping configuration" %
                                                        (i.device_name, machine.resource_id))
                                    failed = True
                                    continue

                                if iface.fabric_id == fabric.resource_id:
                                    self.logger.debug("Interface %s already attached to fabric_id %s" %
                                                        (i.device_name, fabric.resource_id))
                                else:
                                    self.logger.debug("Attaching node %s interface %s to fabric_id %s" %
                                                  (node.name, i.device_name, fabric.resource_id))
                                    iface.attach_fabric(fabric_id=fabric.resource_id)

                                for iface_net in getattr(i, 'networks', []):
                                    dd_net = site_design.get_network(iface_net)

                                    if dd_net is not None:
                                        link_iface = None
                                        if iface_net == getattr(nl, 'native_network', None):
                                            # If a node interface is attached to the native network for a link
                                            # then the interface itself should be linked to network, not a VLAN
                                            # tagged interface
                                            self.logger.debug("Attaching node %s interface %s to untagged VLAN on fabric %s" %
                                                              (node.name, i.device_name, fabric.resource_id))
                                            link_iface = iface
                                        else:
                                            # For non-native networks, we create VLAN tagged interfaces as children
                                            # of this interface                                
                                            vlan_options = { 'vlan_tag': dd_net.vlan_id,
                                                             'parent_name': iface.name,
                                                           }

                                            if dd_net.mtu is not None:
                                                vlan_options['mtu'] = dd_net.mtu

                                            self.logger.debug("Creating tagged interface for VLAN %s on system %s interface %s" %
                                                              (dd_net.vlan_id, node.name, i.device_name))

                                            link_iface = machine.interfaces.create_vlan(**vlan_options)

                                        link_options = {}
                                        link_options['primary'] = True if iface_net == getattr(node, 'primary_network', None) else False
                                        link_options['subnet_cidr'] = dd_net.cidr

                                        found = False
                                        for a in getattr(node, 'addressing', []):
                                            if a.network == iface_net:
                                                link_options['ip_address'] = 'dhcp' if a.type == 'dhcp' else a.address
                                                found = True

                                        if not found:
                                            self.logger.warning("No addressed assigned to network %s for node %s, link is L2 only." %
                                                               (iface_net, node.name))
                                            link_options['ip_address'] = None

                                        self.logger.debug("Linking system %s interface %s to subnet %s" %
                                                          (node.name, i.device_name, dd_net.cidr))

                                        link_iface.link_subnet(**link_options)
                                        worked = True
                                    else:
                                        failed=True
                                        self.logger.error("Did not find a defined Network %s to attach to interface" % iface_net)

                        elif machine.status_name == 'Broken':
                            self.logger.info("Located node %s in MaaS, status broken. Run ConfigureHardware before configurating network" % (n))
                            result_detail['detail'].append("Located node %s in MaaS, status 'Broken'. Skipping..." % (n))
                            failed = True
                        else:
                            self.logger.warning("Located node %s in MaaS, unknown status %s. Skipping..." % (n, machine.status_name))
                            result_detail['detail'].append("Located node %s in MaaS, unknown status %s. Skipping..." % (n, machine.status_name))
                            failed = True
                    else:
                        self.logger.warning("Node %s not found in MaaS" % n)
                        failed = True
                        result_detail['detail'].append("Node %s not found in MaaS" % n)

                except Exception as ex:
                    failed = True
                    self.logger.error("Error configuring network for node %s: %s" % (n, str(ex)))
                    result_detail['detail'].append("Error configuring network for node %s: %s" % (n, str(ex)))

            if failed:
                final_result = hd_fields.ActionResult.Failure
            else:
                final_result = hd_fields.ActionResult.Success

            self.orchestrator.task_field_update(self.task.get_id(),
                                status=hd_fields.TaskStatus.Complete,
                                result=final_result,
                                result_detail=result_detail)
        elif task_action == hd_fields.OrchestratorAction.ApplyNodePlatform:
            try:
                machine_list = maas_machine.Machines(self.maas_client)
                machine_list.refresh()

                tag_list = maas_tag.Tags(self.maas_client)
                tag_list.refresh()
            except Exception as ex:
                self.logger.error("Error deploying node, cannot access MaaS: %s" % str(ex))
                traceback.print_tb(sys.last_traceback)
                self.orchestrator.task_field_update(self.task.get_id(),
                            status=hd_fields.TaskStatus.Complete,
                            result=hd_fields.ActionResult.Failure,
                            result_detail={'detail': 'Error accessing MaaS API', 'retry': True})
                return

            nodes = self.task.node_list

            result_detail = {'detail': []}

            worked = failed = False

            for n in nodes:
                try:
                    self.logger.debug("Locating node %s for platform configuration" % (n))

                    node = site_design.get_baremetal_node(n)
                    machine = machine_list.identify_baremetal_node(node, update_name=False)

                    if machine is None:
                        self.logger.warning("Could not locate machine for node %s" % n)
                        result_detail['detail'].append("Could not locate machine for node %s" % n)
                        failed = True
                        continue
                except Exception as ex1:
                    failed = True
                    self.logger.error("Error locating machine for node %s: %s" % (n, str(ex1)))
                    result_detail['detail'].append("Error locating machine for node %s" % (n))
                    continue

                try:    
                    # Render the string of all kernel params for the node
                    kp_string = ""

                    for k,v in getattr(node, 'kernel_params', {}).items():
                        if v == 'True':
                            kp_string = kp_string + " %s" % (k)
                        else:
                            kp_string = kp_string + " %s=%s" % (k, v)

                    if kp_string:
                        # Check if the node has an existing kernel params tag
                        node_kp_tag = tag_list.select("%s_kp" % (node.name))
                        self.logger.info("Configuring kernel parameters for node %s" % (node.name))

                        if node_kp_tag is None:
                            self.logger.debug("Creating kernel_params tag for node %s: %s" % (node.name, kp_string))
                            node_kp_tag = maas_tag.Tag(self.maas_client, name="%s_kp" % (node.name), kernel_opts=kp_string)
                            node_kp_tag = tag_list.add(node_kp_tag)
                            node_kp_tag.apply_to_node(machine.resource_id)
                        else:
                            self.logger.debug("Updating tag %s for node %s: %s" % (node_kp_tag.resource_id, node.name, kp_string))
                            node_kp_tag.kernel_opts = kp_string
                            node_kp_tag.update()

                        self.logger.info("Applied kernel parameters to node %s" % n)
                        result_detail['detail'].append("Applied kernel parameters to node %s" % (node.name))
                        worked = True
                except Exception as ex2:
                    failed = True
                    result_detail['detail'].append("Error configuring kernel parameters for node %s" % (n))
                    self.logger.error("Error configuring kernel parameters for node %s: %s" % (n, str(ex2)))
                    continue

                try:
                    if node.tags is not None and len(node.tags) > 0:
                        self.logger.info("Configuring static tags for node %s" % (node.name))

                        for t in node.tags:
                            tag_list.refresh()
                            tag = tag_list.select(t)

                            if tag is None:
                                try:
                                    self.logger.debug("Creating static tag %s" % t)
                                    tag = maas_tag.Tag(self.maas_client, name=t)
                                    tag = tag_list.add(tag)
                                except errors.DriverError as dex:
                                    tag_list.refresh()
                                    tag = tag_list.select(t)
                                    if tag is not None:
                                        self.logger.debug("Tag %s arrived out of nowhere." % t)
                                    else:
                                        self.logger.error("Error creating tag %s." % t)
                                        continue

                            self.logger.debug("Applying tag %s to node %s" % (tag.resource_id, machine.resource_id))
                            tag.apply_to_node(machine.resource_id)

                        self.logger.info("Applied static tags to node %s" % (node.name))
                        result_detail['detail'].append("Applied static tags to node %s" % (node.name))
                        worked = True
                except Exception as ex3:
                    failed = True
                    result_detail['detail'].append("Error configuring static tags for node %s" % (node.name))
                    self.logger.error("Error configuring static tags for node %s: %s" % (node.name, str(ex3)))
                    continue

            if failed:
                final_result = hd_fields.ActionResult.Failure
            else:
                final_result = hd_fields.ActionResult.Success

            self.orchestrator.task_field_update(self.task.get_id(),
                                status=hd_fields.TaskStatus.Complete,
                                result=final_result,
                                result_detail=result_detail)
        elif task_action == hd_fields.OrchestratorAction.DeployNode:
            try:
                machine_list = maas_machine.Machines(self.maas_client)
                machine_list.refresh()
 
                fabrics = maas_fabric.Fabrics(self.maas_client)
                fabrics.refresh()

                subnets = maas_subnet.Subnets(self.maas_client)
                subnets.refresh()
            except Exception as ex:
                self.logger.error("Error deploying node, cannot access MaaS: %s" % str(ex))
                traceback.print_tb(sys.last_traceback)
                self.orchestrator.task_field_update(self.task.get_id(),
                            status=hd_fields.TaskStatus.Complete,
                            result=hd_fields.ActionResult.Failure,
                            result_detail={'detail': 'Error accessing MaaS API', 'retry': True})
                return

            nodes = self.task.node_list

            result_detail = {'detail': []}

            worked = failed = False

            for n in nodes:
                self.logger.info("Acquiring node %s for deployment" % (n))

                try:
                    node = site_design.get_baremetal_node(n)
                    machine = machine_list.identify_baremetal_node(node, update_name=False)
                    if machine.status_name == 'Deployed':
                        self.logger.info("Node %s already deployed, skipping." % (n))
                        continue
                    elif machine.status_name == 'Ready':
                        machine = machine_list.acquire_node(n)
                    else:
                        self.logger.warning("Unexpected status %s for node %s, skipping deployment." % (machine.status_name, n))
                        continuek
                except errors.DriverError as dex:
                    self.logger.warning("Error acquiring node %s, skipping" % n)
                    failed = True
                    continue

                # Need to create bootdata keys for all the nodes being deployed
                # TODO this should be in the orchestrator
                node = site_design.get_baremetal_node(n)
                data_key = str(uuid.uuid4())
                self.state_manager.set_bootdata_key(n, self.task.design_id, data_key)
                node.owner_data['bootdata_key'] = data_key
                self.logger.debug("Configured bootdata for node %s" % (n))

                # Set owner data in MaaS
                try:
                    self.logger.info("Setting node %s owner data." % n)
                    for k,v in node.owner_data.items():
                        self.logger.debug("Set owner data %s = %s for node %s" % (k, v, n))
                        machine.set_owner_data(k, v)
                except Exception as ex:
                    self.logger.warning("Error setting node %s owner data: %s" % (n, str(ex)))
                    failed = True
                    continue

                self.logger.info("Deploying node %s" % (n))

                try:
                    machine.deploy()
                except DriverError as dex:
                    self.logger.warning("Error deploying node %s, skipping" % n)
                    failed = True
                    continue

                attempts = 0
                max_attempts = cfg.CONF.timeouts.deploy_node * (60 // cfg.CONF.maasdriver.poll_interval)

                while (attempts < max_attempts and 
                          ( not machine.status_name.startswith('Deployed') and not machine.status_name.startswith('Failed'))):
                    attempts = attempts + 1
                    time.sleep(cfg.CONF.maasdriver.poll_interval)
                    try:
                        machine.refresh()
                        self.logger.debug("Polling node %s status attempt %d of %d: %s" % (n, attempts, max_attempts, machine.status_name))
                    except:
                        self.logger.warning("Error updating node %s status during commissioning, will re-attempt." %
                                             (n))
                if machine.status_name.startswith('Deployed'):
                    result_detail['detail'].append("Node %s deployed" % (n))
                    self.logger.info("Node %s deployed" % (n))
                    worked = True
                else:
                    result_detail['detail'].append("Node %s deployment timed out" % (n))
                    self.logger.warning("Node %s deployment timed out." % (n))
                    failed = True

            if worked and failed:
                final_result = hd_fields.ActionResult.PartialSuccess
            elif failed:
                final_result = hd_fields.ActionResult.Failure
            else:
                final_result = hd_fields.ActionResult.Success

            self.orchestrator.task_field_update(self.task.get_id(),
                                status=hd_fields.TaskStatus.Complete,
                                result=final_result,
                                result_detail=result_detail)

def list_opts():
    return {MaasNodeDriver.driver_key: MaasNodeDriver.maasdriver_options}

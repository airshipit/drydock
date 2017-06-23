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

import drydock_provisioner.error as errors
import drydock_provisioner.config as config
import drydock_provisioner.drivers as drivers
import drydock_provisioner.objects.fields as hd_fields
import drydock_provisioner.objects.task as task_model

from drydock_provisioner.drivers.node import NodeDriver
from .api_client import MaasRequestFactory
import drydock_provisioner.drivers.node.maasdriver.models.fabric as maas_fabric
import drydock_provisioner.drivers.node.maasdriver.models.vlan as maas_vlan
import drydock_provisioner.drivers.node.maasdriver.models.subnet as maas_subnet
import drydock_provisioner.drivers.node.maasdriver.models.machine as maas_machine

class MaasNodeDriver(NodeDriver):

    def __init__(self, **kwargs):
        super(MaasNodeDriver, self).__init__(**kwargs)
	
        self.driver_name = "maasdriver"
        self.driver_key = "maasdriver"
        self.driver_desc = "MaaS Node Provisioning Driver"

        self.config = config.DrydockConfig.node_driver[self.driver_key]

        self.logger = logging.getLogger('drydock.nodedriver.maasdriver')

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
            maas_client = MaasRequestFactory(self.config['api_url'], self.config['api_key']) 

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
                        task_id=subtask.get_id(),config=self.config)

            self.logger.info("Starting thread for task %s to create network templates" % (subtask.get_id()))

            runner.start()

            # TODO Figure out coherent system for putting all the timeouts in
            # the config

            runner.join(timeout=120)

            if runner.is_alive():
                result =  {
                    'retry': False,
                    'detail': 'MaaS Network creation timed-out'
                }

                self.logger.warn("Thread for task %s timed out after 120s" % (subtask.get_id()))
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
                'detail': []
            }

            for n in task.node_list:
                subtask = self.orchestrator.create_task(task_model.DriverTask,
                        parent_task_id=task.get_id(), design_id=design_id,
                        action=hd_fields.OrchestratorAction.IdentifyNode,
                        site_name=task.site_name,
                        task_scope={'site': task.site_name, 'node_names': [n]})
                runner = MaasTaskRunner(state_manager=self.state_manager,
                        orchestrator=self.orchestrator,
                        task_id=subtask.get_id(),config=self.config)

                self.logger.info("Starting thread for task %s to identify node %s" % (subtask.get_id(), n))

                runner.start()
                subtasks.append(subtask.get_id())

            running_subtasks = len(subtasks)
            attempts = 0
            worked = failed = False

            #TODO Add timeout to config
            while running_subtasks > 0 and attempts < 3:
                for t in subtasks:
                    subtask = self.state_manager.get_task(t)

                    if subtask.status == hd_fields.TaskStatus.Complete:
                        self.logger.info("Task %s to identify node %s complete - status %s" %
                                        (subtask.get_id(), n, subtask.get_result()))

                        result_detail['detail'].extend(subtask.result_detail['detail'])
                        running_subtasks = running_subtasks - 1

                        if subtask.result in [hd_fields.ActionResult.Success,
                                           hd_fields.ActionResult.PartialSuccess]:
                            worked = True
                        elif subtask.result in [hd_fields.ActionResult.Failure,
                                             hd_fields.ActionResult.PartialSuccess]:
                            failed = True

                time.sleep(1 * 60)
                attempts = attempts + 1

            if running_subtasks > 0:
                self.logger.warn("Time out for task %s before all subtask threads complete" % (task.get_id()))
                result = hd_fields.ActionResult.DependentFailure
                result_detail['detail'].append('Some subtasks did not complete before the timeout threshold')
            if worked and failed:
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

    def __init__(self, config=None, **kwargs):
        super(MaasTaskRunner, self).__init__(**kwargs)

        self.driver_config = config

        self.logger = logging.getLogger('drydock.nodedriver.maasdriver')

    def execute_task(self):
        task_action = self.task.action

        self.orchestrator.task_field_update(self.task.get_id(),
                            status=hd_fields.TaskStatus.Running,
                            result=hd_fields.ActionResult.Incomplete)

        self.maas_client = MaasRequestFactory(self.driver_config['api_url'],
                                              self.driver_config['api_key'])

        site_design = self.orchestrator.get_effective_site(self.task.design_id)

        if task_action == hd_fields.OrchestratorAction.CreateNetworkTemplate:
            # Try to true up MaaS definitions of fabrics/vlans/subnets
            # with the networks defined in Drydock
            design_networks = site_design.networks

            subnets = maas_subnet.Subnets(self.maas_client)
            subnets.refresh()

            result_detail = {
                'detail': []
            }

            for n in design_networks:
                try:
                    subnet = subnets.singleton({'cidr': n.cidr})

                    if subnet is not None:
                        subnet.name = n.name
                        subnet.dns_servers = n.dns_servers

                        vlan_list = maas_vlan.Vlans(self.maas_client, fabric_id=subnet.fabric)
                        vlan_list.refresh()

                        vlan = vlan_list.select(subnet.vlan)

                        if vlan is not None:
                            if ((n.vlan_id is None and vlan.vid != 0) or 
                                (n.vlan_id is not None and vlan.vid != n.vlan_id)):

                                # if the VLAN name matches, assume this is the correct resource
                                # and it needs to be updated
                                if vlan.name == n.name:
                                    vlan.set_vid(n.vlan_id)
                                    vlan.mtu = n.mtu
                                    vlan.update()
                                    result_detail['detail'].append("VLAN %s found for network %s, updated attributes"
                                                                    % (vlan.resource_id, n.name))
                                else:
                                    # Found a VLAN with the correct VLAN tag, update subnet to use it
                                    target_vlan = vlan_list.singleton({'vid': n.vlan_id if n.vlan_id is not None else 0})
                                    if target_vlan is not None:
                                        subnet.vlan = target_vlan.resource_id
                                    else:
                                        # This is a flag that after creating a fabric and
                                        # VLAN below, update the subnet
                                        subnet.vlan = None
                        else:
                            subnet.vlan = None
            
                        # Check if the routes have a default route
                        subnet.gateway_ip = n.get_default_gateway()


                        result_detail['detail'].append("Subnet %s found for network %s, updated attributes"
                                                % (subnet.resource_id, n.name))

                    # Need to find or create a Fabric/Vlan for this subnet
                    if (subnet is None or (subnet is not None and subnet.vlan is None)):
                        fabric_list = maas_fabric.Fabrics(self.maas_client)
                        fabric_list.refresh()
                        fabric = fabric_list.singleton({'name': n.name})

                        vlan = None
                    
                        if fabric is not None:
                            vlan_list = maas_vlan.Vlans(self.maas_client, fabric_id=fabric.resource_id)
                            vlan_list.refresh()
                        
                            vlan = vlan_list.singleton({'vid': n.vlan_id if n.vlan_id is not None else 0})

                            if vlan is not None:
                                vlan = matching_vlans[0]

                                vlan.name = n.name
                                if getattr(n, 'mtu', None) is not None:
                                    vlan.mtu = n.mtu

                                if subnet is not None:
                                    subnet.vlan = vlan.resource_id
                                    subnet.update()

                                vlan.update()
                                result_detail['detail'].append("VLAN %s found for network %s, updated attributes"
                                                % (vlan.resource_id, n.name))
                            else:
                                # Create a new VLAN in this fabric and assign subnet to it
                                vlan = maas_vlan.Vlan(self.maas_client, name=n.name, vid=vlan_id,
                                                    mtu=getattr(n, 'mtu', None),fabric_id=fabric.resource_id)
                                vlan = vlan_list.add(vlan)

                                result_detail['detail'].append("VLAN %s created for network %s"
                                                                % (vlan.resource_id, n.name))
                                if subnet is not None:
                                    subnet.vlan = vlan.resource_id
                                    subnet.update()

                        else:
                            # Create new fabric and VLAN
                            fabric = maas_fabric.Fabric(self.maas_client, name=n.name)
                            fabric = fabric_list.add(fabric)
                            fabric_list.refresh()

                            result_detail['detail'].append("Fabric %s created for network %s"
                                                                % (fabric.resource_id, n.name))

                            vlan_list = maas_vlan.Vlans(self.maas_client, fabric_id=new_fabric.resource_id)
                            vlan_list.refresh()

                            # A new fabric comes with a single default VLAN. Retrieve it and update attributes
                            vlan = vlan_list.single()

                            vlan.name = n.name
                            vlan.vid = n.vlan_id if n.vlan_id is not None else 0
                            if getattr(n, 'mtu', None) is not None:
                                vlan.mtu = n.mtu

                            vlan.update()
                            result_detail['detail'].append("VLAN %s updated for network %s"
                                                            % (vlan.resource_id, n.name))
                        if subnet is not None:
                            # If subnet was found above, but needed attached to a new fabric/vlan then
                            # attach it
                            subnet.vlan = vlan.resource_id
                            subnet.update()

                    if subnet is None:
                        # If subnet did not exist, create it here and attach it to the fabric/VLAN
                        subnet = maas_subnet.Subnet(self.maas_client, name=n.name, cidr=n.cidr, fabric=fabric.resource_id,
                                                vlan=vlan.resource_id, gateway_ip=n.get_default_gateway())

                        subnet_list = maas_subnet.Subnets(self.maas_client)
                        subnet = subnet_list.add(subnet)
                except ValueError as vex:
                    raise errors.DriverError("Inconsistent data from MaaS")
                    
            subnet_list = maas_subnet.Subnets(self.maas_client)
            subnet_list.refresh()

            action_result = hd_fields.ActionResult.Incomplete

            success_rate = 0

            for n in design_networks:
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


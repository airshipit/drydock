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
"""Task driver for completing node provisioning with Canonical MaaS 2.2+."""

import time
import logging
import re
import math
import yaml

from datetime import datetime

import drydock_provisioner.error as errors
import drydock_provisioner.config as config
import drydock_provisioner.objects.fields as hd_fields
import drydock_provisioner.objects.hostprofile as hostprofile
import drydock_provisioner.objects as objects

from drydock_provisioner.control.util import get_internal_api_href
from drydock_provisioner.orchestrator.actions.orchestrator import BaseAction
from drydock_provisioner.drivers.node.maasdriver.errors import RackControllerConflict
from drydock_provisioner.drivers.node.maasdriver.errors import ApiNotAvailable

import drydock_provisioner.drivers.node.maasdriver.models.fabric as maas_fabric
import drydock_provisioner.drivers.node.maasdriver.models.vlan as maas_vlan
import drydock_provisioner.drivers.node.maasdriver.models.subnet as maas_subnet
import drydock_provisioner.drivers.node.maasdriver.models.machine as maas_machine
import drydock_provisioner.drivers.node.maasdriver.models.tag as maas_tag
import drydock_provisioner.drivers.node.maasdriver.models.sshkey as maas_keys
import drydock_provisioner.drivers.node.maasdriver.models.boot_resource as maas_boot_res
import drydock_provisioner.drivers.node.maasdriver.models.rack_controller as maas_rack
import drydock_provisioner.drivers.node.maasdriver.models.partition as maas_partition
import drydock_provisioner.drivers.node.maasdriver.models.volumegroup as maas_vg
import drydock_provisioner.drivers.node.maasdriver.models.repository as maas_repo
import drydock_provisioner.drivers.node.maasdriver.models.domain as maas_domain


class BaseMaasAction(BaseAction):
    def __init__(self, *args, maas_client=None):
        super().__init__(*args)

        self.maas_client = maas_client

        self.logger = logging.getLogger(
            config.config_mgr.conf.logging.nodedriver_logger_name)

    def _add_detail_logs(self, node, machine, stage, result_type='all'):
        result_details = machine.get_task_results(result_type=result_type)
        for r in result_details:
            if r.get_decoded_data():
                bd = objects.BuildData(
                    node_name=node.name,
                    task_id=self.task.task_id,
                    collected_date=r.updated,
                    generator="{}:{}".format(stage, r.name),
                    data_format='text/plain',
                    data_element=r.get_decoded_data())
                self.state_manager.post_build_data(bd)
        log_href = "%s/tasks/%s/builddata" % (get_internal_api_href("v1.0"),
                                              str(self.task.task_id))
        self.task.result.add_link('detail_logs', log_href)
        self.task.save()


class ValidateNodeServices(BaseMaasAction):
    """Action to validate MaaS is available and ready for use."""

    def start(self):
        self.task.set_status(hd_fields.TaskStatus.Running)

        try:
            if self.maas_client.test_connectivity():
                self.logger.info("Able to connect to MaaS.")
                self.task.add_status_msg(
                    msg='Able to connect to MaaS.',
                    error=False,
                    ctx='NA',
                    ctx_type='NA')
                self.task.success()
                if self.maas_client.test_authentication():
                    self.logger.info("Able to authenticate with MaaS API.")
                    self.task.add_status_msg(
                        msg='Able to authenticate with MaaS API.',
                        error=False,
                        ctx='NA',
                        ctx_type='NA')
                    self.task.success()

                    boot_res = maas_boot_res.BootResources(self.maas_client)
                    boot_res.refresh()

                    if boot_res.is_importing():
                        self.logger.info(
                            "MaaS still importing boot resources.")
                        self.task.add_status_msg(
                            msg='MaaS still importing boot resources.',
                            error=True,
                            ctx='NA',
                            ctx_type='NA')
                        self.task.failure()
                    else:
                        if boot_res.len() > 0:
                            self.logger.info("MaaS has synced boot resources.")
                            self.task.add_status_msg(
                                msg='MaaS has synced boot resources.',
                                error=False,
                                ctx='NA',
                                ctx_type='NA')
                            self.task.success()
                        else:
                            self.logger.info("MaaS has no boot resources.")
                            self.task.add_status_msg(
                                msg='MaaS has no boot resources.',
                                error=True,
                                ctx='NA',
                                ctx_type='NA')
                            self.task.failure()

                    rack_ctlrs = maas_rack.RackControllers(self.maas_client)
                    rack_ctlrs.refresh()

                    if rack_ctlrs.len() == 0:
                        self.logger.info(
                            "No rack controllers registered in MaaS")
                        self.task.add_status_msg(
                            msg='No rack controllers registered in MaaS',
                            error=True,
                            ctx='NA',
                            ctx_type='NA')
                        self.task.failure()
                    else:
                        healthy_rackd = []
                        for r in rack_ctlrs:
                            if r.is_healthy():
                                healthy_rackd.append(r.hostname)
                            else:
                                msg = "Rack controller %s not healthy." % r.hostname
                                self.logger.info(msg)
                                self.task.add_status_msg(
                                    msg=msg,
                                    error=True,
                                    ctx=r.hostname,
                                    ctx_type='rack_ctlr')
                        if not healthy_rackd:
                            msg = "No healthy rack controllers found."
                            self.logger.info(msg)
                            self.task.add_status_msg(
                                msg=msg,
                                error=True,
                                ctx='maas',
                                ctx_type='cluster')
                            self.task.failure()

        except errors.TransientDriverError as ex:
            self.task.add_status_msg(
                msg=str(ex), error=True, ctx='NA', ctx_type='NA', retry=True)
            self.task.failure()
        except errors.PersistentDriverError as ex:
            self.task.add_status_msg(
                msg=str(ex), error=True, ctx='NA', ctx_type='NA')
            self.task.failure()
        except Exception as ex:
            self.task.add_status_msg(
                msg=str(ex), error=True, ctx='NA', ctx_type='NA')
            self.task.failure()

        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.save()
        return


class CreateStorageTemplate(BaseMaasAction):
    """Action for any site wide storage activity, not implemented."""

    def start(self):
        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.failure()
        self.task.save()
        return


class CreateBootMedia(BaseMaasAction):
    """Action to import image resources."""

    def start(self):
        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.failure()
        self.task.save()
        return


class PrepareHardwareConfig(BaseMaasAction):
    """Action to prepare commissioning configuration."""

    def start(self):
        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.failure()
        self.task.save()
        return


class InterrogateNode(BaseMaasAction):
    """Action to query MaaS for build-time information about the node."""

    def start(self):
        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.failure()
        self.task.save()
        return


class DestroyNode(BaseMaasAction):
    """Action to remove node from MaaS in preparation for redeploy."""

    # define the list of node statuses, from which maas server allows releasing a node

    # A machine can be released from following states, based on MaaS API reference.
    # The disk of the released machine is erased, and the machine will end up in
    # "Ready" state in MaaS after release.
    actionable_node_statuses = (
        "Allocated",
        "Deployed",
        "Deploying",
        "Failed deployment",
        "Releasing failed",
        "Failed disk erasing",
    )

    def start(self):
        """
        Destroy Node erases the storage, releases the BM node in MaaS, and
        finally deletes the BM node as a resource from the MaaS database.
        After successful completion of this action, the destroyed nodes are removed
        from MaaS list of resources and will be Unkown to MaaS. These nodes have
        to go through the enlistment process and be detected by MaaS as new nodes.
        Destroy Node can be performed from any BM node state.

        :return: None
        """
        try:
            machine_list = maas_machine.Machines(self.maas_client)
            machine_list.refresh()
        except Exception as ex:
            self.logger.warning("Error accessing the MaaS API.", exc_info=ex)
            self.task.set_status(hd_fields.TaskStatus.Complete)
            self.task.failure()
            self.task.add_status_msg(
                msg='Error accessing MaaS Machines API: {}'.format(str(ex)),
                error=True,
                ctx='NA',
                ctx_type='NA')
            self.task.save()
            return

        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()

        try:
            site_design = self._load_site_design()
        except errors.OrchestratorError:
            self.task.add_status_msg(
                msg="Error loading site design.",
                error=True,
                ctx='NA',
                ctx_type='NA')
            self.task.set_status(hd_fields.TaskStatus.Complete)
            self.task.failure()
            self.task.save()
            return

        nodes = self.orchestrator.process_node_filter(self.task.node_filter,
                                                      site_design)
        for n in nodes:
            try:
                machine = find_node_in_maas(self.maas_client, n)

                if machine is None:
                    msg = "Could not locate machine for node {}".format(n.name)
                    self.logger.info(msg)
                    self.task.add_status_msg(
                        msg=msg, error=False, ctx=n.name, ctx_type='node')
                    self.task.success(focus=n.get_id())
                    continue
                elif type(machine) == maas_rack.RackController:
                    msg = "Cannot delete rack controller {}.".format(n.name)
                    self.logger.info(msg)
                    self.task.add_status_msg(
                        msg=msg, error=False, ctx=n.name, ctx_type='node')
                    self.task.failure(focus=n.get_id())
                    continue

                # First release the node and erase its disks, if MaaS API allows
                if machine.status_name in self.actionable_node_statuses:
                    msg = "Releasing node {}, and erasing storage.".format(
                        n.name)
                    self.logger.info(msg)

                    try:
                        machine.release(erase_disk=True, quick_erase=True)
                    except errors.DriverError:
                        msg = "Error Releasing node {}, skipping".format(
                            n.name)
                        self.logger.warning(msg)
                        self.task.add_status_msg(
                            msg=msg, error=True, ctx=n.name, ctx_type='node')
                        self.task.failure(focus=n.get_id())
                        continue

                    # node release with erase disk will take sometime monitor it
                    attempts = 0
                    max_attempts = (
                        config.config_mgr.conf.timeouts.destroy_node
                        * 60) // config.config_mgr.conf.maasdriver.poll_interval

                    while (attempts < max_attempts
                            and (not machine.status_name.startswith('Ready')
                                 and not
                                 machine.status_name.startswith('Failed'))):
                        attempts = attempts + 1
                        time.sleep(
                            config.config_mgr.conf.maasdriver.poll_interval)
                        try:
                            machine.refresh()
                            self.logger.debug(
                                "Polling node {} status attempt {:d} of {:d}: {}"
                                .format(n.name, attempts, max_attempts,
                                        machine.status_name))
                        except Exception:
                            self.logger.warning(
                                "Error updating node {} status during release node, will re-attempt."
                                .format(n.name))
                    if machine.status_name.startswith('Ready'):
                        msg = "Node {} released and disk erased.".format(
                            n.name)
                        self.logger.info(msg)
                        self.task.add_status_msg(
                            msg=msg, error=False, ctx=n.name, ctx_type='node')
                        self.task.success(focus=n.get_id())
                    else:
                        msg = "Node {} release timed out".format(n.name)
                        self.logger.warning(msg)
                        self.task.add_status_msg(
                            msg=msg, error=True, ctx=n.name, ctx_type='node')
                        self.task.failure(focus=n.get_id())
                else:
                    # Node is in a state that cannot be released from MaaS API.
                    # Reset the storage instead
                    msg = "Destroy node {} in status: {}, resetting storage.".format(
                        n.name, machine.status_name)
                    self.logger.info(msg)
                    machine.reset_storage_config()
                    self.task.add_status_msg(
                        msg=msg, error=False, ctx=n.name, ctx_type='node')

                # for both cases above delete the node to force re-commissioning
                # But, before deleting the node reset it power type in maas if
                # the node power type should be virsh.
                try:
                    if n.oob_type == 'libvirt':
                        self.logger.info(
                            'Resetting MaaS virsh power parameters for node {}.'
                            .format(n.name))
                        # setting power type attibutes to empty string
                        # will remove them from maas BMC table
                        machine.reset_power_parameters()
                except AttributeError:
                    pass

                machine.delete()
                msg = "Deleted Node: {} in status: {}.".format(
                    n.name, machine.status_name)
                self.logger.info(msg)
                self.task.add_status_msg(
                    msg=msg, error=False, ctx=n.name, ctx_type='node')
                self.task.success(focus=n.get_id())

            except errors.DriverError as dex:
                msg = "Driver error, while destroying node {}, skipping".format(
                    n.name)
                self.logger.warning(msg, exc_info=dex)
                self.task.add_status_msg(
                    msg=msg, error=True, ctx=n.name, ctx_type='node')
                self.task.failure(focus=n.get_id())
                continue

        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.save()
        return


class CreateNetworkTemplate(BaseMaasAction):
    """Action for configuring the site wide network topology in MaaS."""

    def start(self):
        # TODO(sh8121att) Break this down into more functions
        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()

        try:
            site_design = self._load_site_design()
        except errors.OrchestratorError:
            self.task.add_status_msg(
                msg="Error loading site design.",
                error=True,
                ctx='NA',
                ctx_type='NA')
            self.task.set_status(hd_fields.TaskStatus.Complete)
            self.task.failure()
            self.task.save()
            return

        if not site_design.network_links:
            msg = ("Site design has no network links, no work to do.")
            self.logger.debug(msg)
            self.task.add_status_msg(
                msg=msg, error=False, ctx='NA', ctx_type='NA')
            self.task.success()
            self.task.set_status(hd_fields.TaskStatus.Complete)
            self.task.save()
            return

        # Try to true up MaaS definitions of fabrics/vlans/subnets
        # with the networks defined in Drydock
        design_networks = list()
        design_links = site_design.network_links or []

        fabrics = maas_fabric.Fabrics(self.maas_client)
        fabrics.refresh()

        subnets = maas_subnet.Subnets(self.maas_client)
        subnets.refresh()

        domains = maas_domain.Domains(self.maas_client)
        domains.refresh()

        for design_link in design_links:
            if design_link.metalabels is not None:
                # TODO(sh8121att): move metalabels into config
                if 'noconfig' in design_link.metalabels:
                    self.logger.info(
                        "NetworkLink %s marked 'noconfig', skipping configuration including allowed networks."
                        % (design_link.name))
                    continue

            fabrics_found = set()

            # First loop through the possible Networks on this NetworkLink
            # and validate that MaaS's self-discovered networking matches
            # our design. This means all self-discovered networks that are matched
            # to a link need to all be part of the same fabric. Otherwise there is no
            # way to reconcile the discovered topology with the designed topology
            for net_name in design_link.allowed_networks:
                n = site_design.get_network(net_name)

                if n is None:
                    msg = "Network %s allowed on link %s, but not defined." % (
                        net_name, design_link.name)
                    self.logger.warning(msg)
                    self.task.add_status_msg(
                        msg=msg,
                        error=True,
                        ctx=design_link.name,
                        ctx_type='network_link')
                    continue

                maas_net = subnets.singleton({'cidr': n.cidr})

                if maas_net is not None:
                    fabrics_found.add(maas_net.fabric)

            if len(fabrics_found) > 1:
                msg = "MaaS self-discovered network incompatible with NetworkLink %s" % design_link.name
                self.logger.warning(msg)
                self.task.add_status_msg(
                    msg=msg, error=True, ctx=design_link.name, ctx_type='network_link')
                continue
            elif len(fabrics_found) == 1:
                link_fabric_id = fabrics_found.pop()
                link_fabric = fabrics.select(link_fabric_id)
                link_fabric.name = design_link.name
                link_fabric.update()
            else:
                link_fabric = fabrics.singleton({'name': design_link.name})

                if link_fabric is None:
                    link_fabric = maas_fabric.Fabric(
                        self.maas_client, name=design_link.name)
                    link_fabric = fabrics.add(link_fabric)

            # Ensure that the MTU of the untagged VLAN on the fabric
            # matches that on the NetworkLink config

            vlan_list = maas_vlan.Vlans(
                self.maas_client, fabric_id=link_fabric.resource_id)
            vlan_list.refresh()
            msg = "Updating native VLAN MTU = %d on network link %s" % (design_link.mtu,
                                                                        design_link.name)
            self.logger.debug(msg)
            self.task.add_status_msg(
                msg=msg, error=False, ctx=design_link.name, ctx_type='network_link')
            vlan = vlan_list.singleton({'vid': 0})
            if vlan:
                vlan.mtu = design_link.mtu
                vlan.update()
            else:
                self.logger.warning("Unable to find native VLAN on fabric %s."
                                    % link_fabric.resource_id)

            # Now that we have the fabrics sorted out, check
            # that VLAN tags and subnet attributes are correct
            for net_name in design_link.allowed_networks:
                n = site_design.get_network(net_name)
                design_networks.append(n)

                if n is None:
                    continue

                try:
                    domain = domains.singleton({'name': n.dns_domain})

                    if not domain:
                        self.logger.info(
                            'Network domain not found, adding: %s',
                            n.dns_domain)
                        domain = maas_domain.Domain(
                            self.maas_client,
                            name=n.dns_domain,
                            authoritative=False)
                        domain = domains.add(domain)
                        domains.refresh()

                    subnet = subnets.singleton({'cidr': n.cidr})

                    if subnet is None:
                        msg = "Subnet for network %s not found, creating..." % (
                            n.name)
                        self.logger.info(msg)
                        self.task.add_status_msg(
                            msg=msg, error=False, ctx='NA', ctx_type='NA')

                        fabric_list = maas_fabric.Fabrics(self.maas_client)
                        fabric_list.refresh()
                        fabric = fabric_list.singleton({'name': design_link.name})

                        if fabric is not None:
                            vlan_list = maas_vlan.Vlans(
                                self.maas_client, fabric_id=fabric.resource_id)
                            vlan_list.refresh()

                            vlan = vlan_list.singleton({
                                'vid':
                                n.vlan_id if n.vlan_id is not None else 0
                            })

                            if vlan is not None:
                                vlan.name = n.name

                                if getattr(n, 'mtu', None) is not None:
                                    vlan.mtu = n.mtu

                                vlan.update()
                                msg = "VLAN %s found for network %s, updated attributes" % (
                                    vlan.resource_id, n.name)
                                self.logger.debug(msg)
                                self.task.add_status_msg(
                                    msg=msg,
                                    error=False,
                                    ctx=n.name,
                                    ctx_type='network')
                            else:
                                # Create a new VLAN in this fabric and assign subnet to it
                                vlan = maas_vlan.Vlan(
                                    self.maas_client,
                                    name=n.name,
                                    vid=n.vlan_id,
                                    mtu=getattr(n, 'mtu', None),
                                    fabric_id=fabric.resource_id)
                                vlan = vlan_list.add(vlan)

                                msg = "VLAN %s created for network %s" % (
                                    vlan.resource_id, n.name)
                                self.logger.debug(msg)
                                self.task.add_status_msg(
                                    msg=msg,
                                    error=False,
                                    ctx=n.name,
                                    ctx_type='network')

                            # If subnet did not exist, create it here and attach it to the fabric/VLAN
                            subnet = maas_subnet.Subnet(
                                self.maas_client,
                                name=n.name,
                                cidr=n.cidr,
                                dns_servers=n.dns_servers,
                                fabric=fabric.resource_id,
                                vlan=vlan.resource_id,
                                gateway_ip=n.get_default_gateway())

                            subnet_list = maas_subnet.Subnets(self.maas_client)
                            subnet = subnet_list.add(subnet)

                            msg = "Created subnet %s for CIDR %s on VLAN %s" % (
                                subnet.resource_id, subnet.cidr, subnet.vlan)
                            self.logger.debug(msg)
                            self.task.add_status_msg(
                                msg=msg,
                                error=False,
                                ctx=n.name,
                                ctx_type='network')
                        else:
                            msg = "Fabric %s should be created, but cannot locate it." % (
                                design_link.name)
                            self.logger.error(msg)
                            self.task.add_status_msg(
                                msg=msg,
                                error=True,
                                ctx=n.name,
                                ctx_type='network_link')
                    else:
                        subnet.name = n.name
                        subnet.dns_servers = n.dns_servers

                        msg = "Subnet %s found for network %s, updated attributes" % (
                            subnet.resource_id, n.name)
                        self.task.add_status_msg(
                            msg=msg,
                            error=False,
                            ctx=n.name,
                            ctx_type='network')
                        self.logger.info(msg)

                        vlan_list = maas_vlan.Vlans(
                            self.maas_client, fabric_id=subnet.fabric)
                        vlan_list.refresh()

                        vlan = vlan_list.select(subnet.vlan)

                        if vlan is not None:
                            vlan.name = n.name
                            vlan.set_vid(n.vlan_id)

                            if getattr(n, 'mtu', None) is not None:
                                vlan.mtu = n.mtu

                            vlan.update()
                            msg = "VLAN %s found for network %s, updated attributes" % (
                                vlan.resource_id, n.name)
                            self.logger.debug(msg)
                            self.task.add_status_msg(
                                msg=msg,
                                error=False,
                                ctx=n.name,
                                ctx_type='network')
                        else:
                            msg = "MaaS subnet %s does not have a matching VLAN" % (
                                subnet.resource_id)
                            self.logger.error(msg)
                            self.task.add_status_msg(
                                msg=msg,
                                error=True,
                                ctx=n.name,
                                ctx_type='network')
                            self.task.failure(focus=n.name)

                    # Check if the routes have a default route
                    subnet.gateway_ip = n.get_default_gateway()
                    subnet.update()

                    dhcp_on = False

                    for r in n.ranges:
                        try:
                            subnet.add_address_range(r)
                            if r.get('type', None) == 'dhcp':
                                dhcp_on = True
                        except Exception as e:
                            msg = "Error adding range to network %s: %s" % (
                                n.name, str(r))
                            self.logger.error(msg, exc_info=e)
                            self.task.add_status_msg(
                                msg=msg,
                                error=True,
                                ctx=n.name,
                                ctx_type='network')

                    vlan_list = maas_vlan.Vlans(
                        self.maas_client, fabric_id=subnet.fabric)
                    vlan_list.refresh()
                    vlan = vlan_list.select(subnet.vlan)

                    if dhcp_on:
                        # check if design requires a dhcp relay and if the MaaS vlan already uses a dhcp_relay
                        msg = "DHCP enabled for subnet %s, activating in MaaS" % (
                            subnet.name)
                        self.logger.info(msg)
                        self.task.add_status_msg(
                            msg=msg,
                            error=False,
                            ctx=n.name,
                            ctx_type='network')

                        rack_ctlrs = maas_rack.RackControllers(
                            self.maas_client)
                        rack_ctlrs.refresh()

                        # Reset DHCP stuff to avoid offline rack controllers

                        vlan.reset_dhcp_mgmt()
                        dhcp_config_set = False

                        for r in rack_ctlrs:
                            if not r.is_healthy():
                                continue
                            if n.dhcp_relay_upstream_target is not None:
                                if r.interface_for_ip(
                                        n.dhcp_relay_upstream_target):
                                    if not r.is_healthy():
                                        msg = ("Rack controller %s with DHCP relay is not healthy." %
                                               r.hostname)
                                        self.logger.info(msg)
                                        self.task.add_status_msg(
                                            msg=msg,
                                            error=True,
                                            ctx=n.name,
                                            ctx_type='network')
                                        break
                                    iface = r.interface_for_ip(
                                        n.dhcp_relay_upstream_target)
                                    vlan.relay_vlan = iface.vlan
                                    msg = "Relaying DHCP on vlan %s to vlan %s" % (
                                        vlan.resource_id, vlan.relay_vlan)
                                    self.logger.info(msg)
                                    self.task.add_status_msg(
                                        msg=msg,
                                        error=False,
                                        ctx=n.name,
                                        ctx_type='network')
                                    vlan.update()
                                    dhcp_config_set = True
                                    break
                            else:
                                for i in r.interfaces:
                                    if i.vlan == vlan.resource_id:
                                        msg = "Rack controller %s has interface on vlan %s" % (
                                            r.resource_id, vlan.resource_id)
                                        self.logger.debug(msg)
                                        rackctl_id = r.resource_id

                                        if not r.is_healthy():
                                            msg = ("Rack controller %s not healthy, skipping DHCP config." %
                                                   r.resource_id)
                                            self.logger.info(msg)
                                            self.task.add_status_msg(
                                                msg=msg,
                                                error=True,
                                                ctx=n.name,
                                                ctx_type='network')
                                            break
                                        try:
                                            vlan.dhcp_on = True
                                            vlan.add_rack_controller(
                                                rackctl_id)
                                            msg = "Enabling DHCP on VLAN %s managed by rack ctlr %s" % (
                                                vlan.resource_id, rackctl_id)
                                            self.logger.debug(msg)
                                            self.task.add_status_msg(
                                                msg=msg,
                                                error=False,
                                                ctx=n.name,
                                                ctx_type='network')
                                            vlan.update()
                                            dhcp_config_set = True
                                        except RackControllerConflict:
                                            msg = (
                                                "More than two rack controllers on vlan %s, "
                                                "skipping enabling %s." %
                                                (vlan.resource_id, rackctl_id))
                                            self.logger.debug(msg)
                                            self.task.add_status_msg(
                                                msg=msg,
                                                error=False,
                                                ctx=n.name,
                                                ctx_type='network')
                                        break

                        if not dhcp_config_set:
                            msg = "Network %s requires DHCP, but could not locate a rack controller to serve it." % (
                                n.name)
                            self.logger.error(msg)
                            self.task.add_status_msg(
                                msg=msg,
                                error=True,
                                ctx=n.name,
                                ctx_type='network')
                            self.task.failure(focus=n.name)

                except ValueError:
                    raise errors.DriverError("Inconsistent data from MaaS")

        # Now that all networks should be created, we can setup routes between them
        subnet_list = maas_subnet.Subnets(self.maas_client)
        subnet_list.refresh()

        for n in design_networks:
            src_subnet = subnet_list.singleton({'cidr': n.cidr})
            for r in n.routes:
                # care for case of routedomain routes that are logical placeholders
                if not r.get('subnet', None):
                    continue
                route_net = r.get('subnet')
                # Skip the default route case
                if route_net == '0.0.0.0/0':
                    continue
                dest_subnet = subnet_list.singleton({'cidr': route_net})
                if dest_subnet is not None:
                    src_subnet.add_static_route(
                        dest_subnet.resource_id,
                        r.get('gateway'),
                        metric=r.get('metric', 100))
                else:
                    msg = "Could not locate destination network for static route to %s." % route_net
                    self.task.add_status_msg(
                        msg=msg, error=True, ctx=n.name, ctx_type='network')
                    self.task.failure(focus=n.name)
                    self.logger.info(msg)
                    continue

        # now validate that all subnets allowed on a link were created

        for n in design_networks:
            if n.metalabels is not None:
                # TODO(sh8121att): move metalabels into config
                if 'noconfig' in n.metalabels:
                    self.logger.info(
                        "Network %s marked 'noconfig', skipping validation." %
                        (n.name))
                    continue

            exists = subnet_list.singleton({'cidr': n.cidr})
            if exists is not None:
                self.task.success(focus=n.name)
            else:
                msg = "Network %s defined, but not found in MaaS after network config task." % n.name
                self.logger.error(msg)
                self.task.add_status_msg(
                    msg=msg, error=True, ctx=n.name, ctx_type='network')
                self.task.failure(focus=n.name)

        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.save()
        return


class ConfigureNodeProvisioner(BaseMaasAction):
    """Action for configuring site-wide node provisioner options."""
    # These repo names cannot be deleted out of MAAS
    # and maintain functionality
    DEFAULT_REPOS = ['main_archive', 'ports_archive']

    def start(self):
        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()

        try:
            site_design = self._load_site_design()
        except errors.OrchestratorError:
            self.task.add_status_msg(
                msg="Error loading site design.",
                error=True,
                ctx='NA',
                ctx_type='NA')
            self.task.set_status(hd_fields.TaskStatus.Complete)
            self.task.failure()
            self.task.save()
            return

        try:
            current_repos = maas_repo.Repositories(self.maas_client)
            current_repos.refresh()
        except Exception as ex:
            self.logger.debug("Error accessing the MaaS API.", exc_info=ex)
            self.task.set_status(hd_fields.TaskStatus.Complete)
            self.task.failure()
            self.task.add_status_msg(
                msg='Error accessing MaaS SshKeys API',
                error=True,
                ctx='NA',
                ctx_type='NA')
            self.task.save()
            return

        site_model = site_design.get_site()

        repo_list = getattr(site_model, 'repositories', None) or []

        if repo_list:
            for r in repo_list:
                try:
                    existing_repo = current_repos.singleton({
                        'name': r.get_id()
                    })
                    new_repo = self.create_maas_repo(self.maas_client, r)
                    if existing_repo:
                        new_repo.resource_id = existing_repo.resource_id
                        new_repo.update()
                        msg = "Updating repository definition for %s." % (
                            r.name)
                        self.logger.debug(msg)
                        self.task.add_status_msg(
                            msg=msg, error=False, ctx='NA', ctx_type='NA')
                        self.task.success()
                    else:
                        new_repo = current_repos.add(new_repo)
                        msg = "Adding repository definition for %s." % (r.name)
                        self.logger.debug(msg)
                        self.task.add_status_msg(
                            msg=msg, error=False, ctx='NA', ctx_type='NA')
                        self.task.success()
                except Exception as ex:
                    msg = "Error adding repository to MaaS configuration: %s" % str(
                        ex)
                    self.logger.warning(msg)
                    self.task.add_status_msg(
                        msg=msg, error=True, ctx='NA', ctx_type='NA')
                    self.task.failure()
            if repo_list.remove_unlisted:
                defined_repos = [x.get_id() for x in repo_list]
                to_delete = [
                    r for r in current_repos if r.name not in defined_repos
                ]
                for r in to_delete:
                    if r.name not in self.DEFAULT_REPOS:
                        r.delete()
                current_repos.refresh()
        else:
            msg = ("No repositories to add, no work to do.")
            self.logger.debug(msg)
            self.task.success()
            self.task.add_status_msg(
                msg=msg, error=False, ctx='NA', ctx_type='NA')

        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.save()
        return

    @staticmethod
    def create_maas_repo(api_client, repo_obj):
        """Create a MAAS model of a repo based of a Drydock model.

        If resource_id is specified, assign it the resource_id so the new instance
        can be used to update an existing repo.

        :param api_client: A MAAS API client configured to connect to MAAS
        :param repo_obj: Instance of objects.Repository
        """
        model_fields = dict()
        if repo_obj.distributions:
            model_fields['distributions'] = ','.join(repo_obj.distributions)
        if repo_obj.components:
            if repo_obj.get_id() in ConfigureNodeProvisioner.DEFAULT_REPOS:
                model_fields['disabled_components'] = ','.join(
                    repo_obj.get_disabled_components())
            else:
                model_fields['components'] = ','.join(repo_obj.components)
        if repo_obj.get_disabled_subrepos():
            model_fields['disabled_pockets'] = ','.join(
                repo_obj.get_disabled_subrepos())
        if repo_obj.arches:
            model_fields['arches'] = ','.join(repo_obj.arches)

        model_fields['key'] = repo_obj.gpgkey

        for k in ['name', 'url']:
            model_fields[k] = getattr(repo_obj, k)

        repo_model = maas_repo.Repository(api_client, **model_fields)
        return repo_model


class ConfigureUserCredentials(BaseMaasAction):
    """Action for configuring user public keys."""

    def start(self):
        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()

        try:
            site_design = self._load_site_design()
        except errors.OrchestratorError:
            self.task.add_status_msg(
                msg="Error loading site design.",
                error=True,
                ctx='NA',
                ctx_type='NA')
            self.task.set_status(hd_fields.TaskStatus.Complete)
            self.task.failure()
            self.task.save()
            return

        try:
            current_keys = maas_keys.SshKeys(self.maas_client)
            current_keys.refresh()
        except Exception as ex:
            self.logger.debug("Error accessing the MaaS API.", exc_info=ex)
            self.task.set_status(hd_fields.TaskStatus.Complete)
            self.task.failure()
            self.task.add_status_msg(
                msg='Error accessing MaaS SshKeys API',
                error=True,
                ctx='NA',
                ctx_type='NA')
            self.task.save()
            return

        site_model = site_design.get_site()

        key_list = getattr(site_model, 'authorized_keys', None) or []

        if key_list:
            for k in key_list:
                try:
                    if len(current_keys.query({
                            'key': k.replace("\n", "")
                    })) == 0:
                        new_key = maas_keys.SshKey(self.maas_client, key=k)
                        new_key = current_keys.add(new_key)
                        msg = "Added SSH key %s to MaaS user profile. Will be installed on all deployed nodes." % (
                            k[:16])
                        self.logger.debug(msg)
                        self.task.add_status_msg(
                            msg=msg, error=False, ctx='NA', ctx_type='NA')
                        self.task.success()
                    else:
                        msg = "SSH key %s already exists in MaaS user profile." % k[:
                                                                                    16]
                        self.logger.debug(msg)
                        self.task.add_status_msg(
                            msg=msg, error=False, ctx='NA', ctx_type='NA')
                        self.task.success()
                except Exception as ex:
                    msg = "Error adding SSH key to MaaS user profile: %s" % str(
                        ex)
                    self.logger.warning(msg)
                    self.task.add_status_msg(
                        msg=msg, error=True, ctx='NA', ctx_type='NA')
                    self.task.failure()
        else:
            msg = ("No keys to add, no work to do.")
            self.logger.debug(msg)
            self.task.success()
            self.task.add_status_msg(
                msg=msg, error=False, ctx='NA', ctx_type='NA')

        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.save()
        return


class IdentifyNode(BaseMaasAction):
    """Action to identify a node resource in MaaS matching a node design."""

    def start(self):
        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()

        try:
            site_design = self._load_site_design()
        except errors.OrchestratorError:
            self.task.add_status_msg(
                msg="Error loading site design.",
                error=True,
                ctx='NA',
                ctx_type='NA')
            self.task.set_status(hd_fields.TaskStatus.Complete)
            self.task.failure()
            self.task.save()
            return

        nodes = self.orchestrator.process_node_filter(self.task.node_filter,
                                                      site_design)

        for n in nodes:
            try:
                machine = find_node_in_maas(self.maas_client, n)
                if machine is None:
                    self.task.failure(focus=n.get_id())
                    self.task.add_status_msg(
                        msg="Node %s not found in MaaS" % n.name,
                        error=True,
                        ctx=n.name,
                        ctx_type='node')
                elif type(machine) == maas_machine.Machine:
                    machine.update_identity(n, domain=n.get_domain(site_design))
                    msg = "Node %s identified in MaaS" % n.name
                    self.logger.debug(msg)
                    self.task.add_status_msg(
                        msg=msg,
                        error=False,
                        ctx=n.name,
                        ctx_type='node')
                    self.task.success(focus=n.get_id())
                elif type(machine) == maas_rack.RackController:
                    msg = "Rack controller %s identified in MaaS" % n.name
                    self.logger.debug(msg)
                    self.task.add_status_msg(
                        msg=msg,
                        error=False,
                        ctx=n.name,
                        ctx_type='node')
                    self.task.success(focus=n.get_id())
            except ApiNotAvailable as api_ex:
                self.logger.debug("Error accessing the MaaS API.", exc_info=api_ex)
                self.task.failure()
                self.task.add_status_msg(
                    msg='Error accessing MaaS API: %s' % str(api_ex),
                    error=True,
                    ctx='NA',
                    ctx_type='NA')
                self.task.save()
            except Exception as ex:
                self.logger.debug(
                    "Exception caught in identify node.", exc_info=ex)
                self.task.failure(focus=n.get_id())
                self.task.add_status_msg(
                    msg="Error trying to location %s in MAAS" % n.name,
                    error=True,
                    ctx=n.name,
                    ctx_type='node')

        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.save()
        return

class ConfigureHardware(BaseMaasAction):
    """Action to start commissioning a server."""

    def start(self):
        try:
            machine_list = maas_machine.Machines(self.maas_client)
            machine_list.refresh()
        except Exception as ex:
            self.logger.debug("Error accessing the MaaS API.", exc_info=ex)
            self.task.set_status(hd_fields.TaskStatus.Complete)
            self.task.failure()
            self.task.add_status_msg(
                msg="Error accessing MaaS Machines API: %s" % str(ex),
                error=True,
                ctx='NA',
                ctx_type='NA')
            self.task.save()
            return

        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()

        try:
            site_design = self._load_site_design()
        except errors.OrchestratorError:
            self.task.add_status_msg(
                msg="Error loading site design.",
                error=True,
                ctx='NA',
                ctx_type='NA')
            self.task.set_status(hd_fields.TaskStatus.Complete)
            self.task.failure()
            self.task.save()
            return

        nodes = self.orchestrator.process_node_filter(self.task.node_filter,
                                                      site_design)

        # TODO(sh8121att): Better way of representing the node statuses than static strings
        for n in nodes:
            try:
                self.logger.debug(
                    "Locating node %s for commissioning" % (n.name))
                machine = find_node_in_maas(self.maas_client, n)
                if type(machine) == maas_rack.RackController:
                    msg = "Located node %s in MaaS as rack controller. Skipping." % (
                        n.name)
                    self.logger.info(msg)
                    self.task.add_status_msg(
                        msg=msg, error=False, ctx=n.name, ctx_type='node')
                    self.task.success(focus=n.get_id())
                elif machine is not None:
                    if machine.status_name in [
                            'New', 'Broken', 'Failed commissioning',
                            'Failed testing'
                    ]:
                        self.logger.debug(
                            "Located node %s in MaaS, starting commissioning" %
                            (n.name))
                        machine.commission()

                        # Poll machine status
                        attempts = 0
                        max_attempts = (
                            config.config_mgr.conf.timeouts.configure_hardware
                            * 60
                        ) // config.config_mgr.conf.maasdriver.poll_interval

                        while (attempts < max_attempts
                               and (machine.status_name != 'Ready'
                                    and not
                                    machine.status_name.startswith('Failed'))):
                            attempts = attempts + 1
                            time.sleep(config.config_mgr.conf.maasdriver.
                                       poll_interval)
                            try:
                                machine.refresh()
                                self.logger.debug(
                                    "Polling node %s status attempt %d of %d: %s"
                                    % (n.name, attempts, max_attempts,
                                       machine.status_name))
                            except Exception:
                                self.logger.warning(
                                    "Error updating node %s status during commissioning, will re-attempt."
                                    % (n.name),
                                    exc_info=True)
                        if machine.status_name == 'Ready':
                            msg = "Node %s commissioned." % (n.name)
                            self.logger.info(msg)
                            self.task.add_status_msg(
                                msg=msg,
                                error=False,
                                ctx=n.name,
                                ctx_type='node')
                            self.task.success(focus=n.get_id())
                            self.collect_build_data(machine)
                        else:
                            msg = "Node %s failed commissioning." % (n.name)
                            self.logger.info(msg)
                            self.task.add_status_msg(
                                msg=msg,
                                error=True,
                                ctx=n.name,
                                ctx_type='node')
                            self.task.failure(focus=n.get_id())
                        self._add_detail_logs(
                            n,
                            machine,
                            'commission',
                            result_type='commissioning')
                        self._add_detail_logs(
                            n, machine, 'testing', result_type='testing')
                    elif machine.status_name in ['Commissioning', 'Testing']:
                        msg = "Located node %s in MaaS, node already being commissioned. Skipping..." % (
                            n.name)
                        self.logger.info(msg)
                        self.task.add_status_msg(
                            msg=msg, error=False, ctx=n.name, ctx_type='node')
                        self.task.success(focus=n.get_id())
                    elif machine.status_name in [
                            'Ready', 'Deploying', 'Allocated', 'Deployed'
                    ]:
                        msg = "Located node %s in MaaS, node commissioned. Skipping..." % (
                            n.name)
                        self.logger.info(msg)
                        self.task.add_status_msg(
                            msg=msg, error=False, ctx=n.name, ctx_type='node')
                        self.task.success(focus=n.get_id())
                    else:
                        msg = "Located node %s in MaaS, unknown status %s. Skipping." % (
                            n, machine.status_name)
                        self.logger.warning(msg)
                        self.task.add_status_msg(
                            msg=msg, error=True, ctx=n.name, ctx_type='node')
                        self.task.failure(focus=n.get_id())
                else:
                    msg = "Node %s not found in MaaS" % n.name
                    self.logger.warning(msg)
                    self.task.add_status_msg(
                        msg=msg, error=True, ctx=n.name, ctx_type='node')
                    self.task.failure(focus=n.get_id())
            except Exception as ex:
                msg = "Error commissioning node %s: %s" % (n.name, str(ex))
                self.logger.warning(msg)
                self.logger.debug(
                    "Unhandled exception attempting to commission node.",
                    exc_info=ex)
                self.task.add_status_msg(
                    msg=msg, error=True, ctx=n.name, ctx_type='node')
                self.task.failure(focus=n.get_id())

        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.save()
        return

    def collect_build_data(self, machine):
        """Collect MaaS build data after commissioning."""
        self.logger.debug("Collecting build data for %s" % machine.hostname)
        try:
            data = machine.get_details()
            if data:
                for t, d in data.items():
                    if t in ('lshw', 'lldp'):
                        df = 'text/xml'
                    else:
                        df = 'text/plain'
                    bd = objects.BuildData(
                        node_name=machine.hostname,
                        task_id=self.task.get_id(),
                        generator=t,
                        collected_date=datetime.utcnow(),
                        data_format=df,
                        data_element=d.decode())
                    self.logger.debug(
                        "Saving build data from generator %s" % t)
                    self.state_manager.post_build_data(bd)
                    self.task.add_status_msg(
                        msg="Saving build data element.",
                        error=False,
                        ctx=machine.hostname,
                        ctx_type='node')
        except Exception as ex:
            self.logger.error(
                "Error collecting node build data for %s" % machine.hostname,
                exc_info=ex)


class ApplyNodeNetworking(BaseMaasAction):
    """Action to configure networking on a node."""

    def start(self):
        try:
            machine_list = maas_machine.Machines(self.maas_client)
            machine_list.refresh()

            fabrics = maas_fabric.Fabrics(self.maas_client)
            fabrics.refresh()

            subnets = maas_subnet.Subnets(self.maas_client)
            subnets.refresh()
        except Exception as ex:
            self.logger.debug("Error accessing the MaaS API.", exc_info=ex)
            self.task.set_status(hd_fields.TaskStatus.Complete)
            self.task.failure()
            self.task.add_status_msg(
                msg="Error accessing MaaS API: %s" % str(ex),
                error=True,
                ctx='NA',
                ctx_type='NA')
            self.task.save()
            return

        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()

        try:
            site_design = self._load_site_design(resolve_aliases=True)
        except errors.OrchestratorError:
            self.task.add_status_msg(
                msg="Error loading site design.",
                error=True,
                ctx='NA',
                ctx_type='NA')
            self.task.set_status(hd_fields.TaskStatus.Complete)
            self.task.failure()
            self.task.save()
            return

        nodes = self.orchestrator.process_node_filter(self.task.node_filter,
                                                      site_design)

        # TODO(sh8121att): Better way of representing the node statuses than static strings
        for n in nodes:
            try:
                self.logger.debug(
                    "Locating node %s for network configuration" % (n.name))

                machine = find_node_in_maas(self.maas_client, n)

                if type(machine) is maas_rack.RackController:
                    msg = ("Node %s is a rack controller, skipping deploy action." %
                           n.name)
                    self.logger.debug(msg)
                    self.task.add_status_msg(
                        msg=msg,
                        error=False,
                        ctx=n.name,
                        ctx_type='node')
                    self.task.success(focus=n.name)
                    continue
                elif machine is not None:
                    if machine.status_name.startswith('Failed Dep'):
                        msg = (
                            "Node %s has failed deployment, releasing to try again."
                            % n.name)
                        self.logger.debug(msg)
                        try:
                            machine.release()
                            machine.refresh()
                        except errors.DriverError:
                            msg = (
                                "Node %s could not be released, skipping deployment."
                                % n.name)
                            self.logger.info(msg)
                            self.task.add_status_msg(
                                msg=msg,
                                error=True,
                                ctx=n.name,
                                ctx_type='node')
                            self.task.failure(focus=n.name)
                            continue
                        msg = ("Released failed node %s to retry deployment." %
                               n.name)
                        self.logger.info(msg)
                        self.task.add_status_msg(
                            msg=msg, error=False, ctx=n.name, ctx_type='node')

                    if machine.status_name == 'Ready':
                        msg = "Located node %s in MaaS, starting interface configuration" % (
                            n.name)
                        self.logger.debug(msg)
                        self.task.add_status_msg(
                            msg=msg, error=False, ctx=n.name, ctx_type='node')

                        machine.reset_network_config()
                        machine.refresh()

                        for i in n.interfaces:
                            if not i.network_link:
                                self.logger.debug(
                                    "Interface %s has no network link, skipping configuration."
                                    % (i.device_name))
                                continue

                            nl = site_design.get_network_link(i.network_link)

                            if nl.metalabels is not None:
                                if 'noconfig' in nl.metalabels:
                                    self.logger.info(
                                        "Interface %s connected to NetworkLink %s marked 'noconfig', skipping."
                                        % (i.device_name, nl.name))
                                    continue

                            fabric = fabrics.singleton({'name': nl.name})

                            if fabric is None:
                                msg = "No fabric found for NetworkLink %s" % (
                                    nl.name)
                                self.logger.error(msg)
                                self.task.add_status_msg(
                                    msg=msg,
                                    error=True,
                                    ctx=n.name,
                                    ctx_type='node')
                                self.task.failure(focus=n.name)
                                continue

                            if nl.bonding_mode != hd_fields.NetworkLinkBondingMode.Disabled:
                                if len(i.get_hw_slaves()) > 1:
                                    msg = "Building node %s interface %s as a bond." % (
                                        n.name, i.device_name)
                                    self.logger.debug(msg)
                                    self.task.add_status_msg(
                                        msg=msg,
                                        error=False,
                                        ctx=n.name,
                                        ctx_type='node')
                                    hw_iface_list = i.get_hw_slaves()
                                    hw_iface_logicalname_list = []
                                    for hw_iface in hw_iface_list:
                                        hw_iface_logicalname_list.append(
                                            n.get_logicalname(hw_iface))
                                    iface = machine.interfaces.create_bond(
                                        device_name=i.device_name,
                                        parent_names=hw_iface_logicalname_list,
                                        mtu=nl.mtu,
                                        fabric=fabric.resource_id,
                                        mode=nl.bonding_mode,
                                        monitor_interval=nl.bonding_mon_rate,
                                        downdelay=nl.bonding_down_delay,
                                        updelay=nl.bonding_up_delay,
                                        lacp_rate=nl.bonding_peer_rate,
                                        hash_policy=nl.bonding_xmit_hash)
                                else:
                                    msg = "Network link %s indicates bonding, " \
                                          "interface %s has less than 2 slaves." % \
                                          (nl.name, i.device_name)
                                    self.logger.warning(msg)
                                    self.task.add_status_msg(
                                        msg=msg,
                                        error=True,
                                        ctx=n.name,
                                        ctx_type='node')
                                    self.task.failure(focus=n.name)
                                    continue
                            else:
                                if len(i.get_hw_slaves()) > 1:
                                    msg = "Network link %s disables bonding, interface %s has multiple slaves." % \
                                          (nl.name, i.device_name)
                                    self.logger.warning(msg)
                                    self.task.add_status_msg(
                                        msg=msg,
                                        error=True,
                                        ctx=n.name,
                                        ctx_type='node')
                                    self.task.failure(n.name)
                                    continue
                                elif len(i.get_hw_slaves()) == 0:
                                    msg = "Interface %s has 0 slaves." % (
                                        i.device_name)
                                    self.logger.warning(msg)
                                    self.task.add_status_msg(
                                        msg=msg,
                                        error=True,
                                        ctx=n.name,
                                        ctx_type='node')
                                    self.task.failure(focus=n.name)
                                else:
                                    msg = "Configuring interface %s on node %s" % (
                                        i.device_name, n.name)
                                    self.logger.debug(msg)
                                    self.task.add_status_msg(
                                        msg=msg,
                                        error=False,
                                        ctx=n.name,
                                        ctx_type='node')
                                    hw_iface = i.get_hw_slaves()[0]
                                    # TODO(sh8121att): HardwareProfile device alias integration
                                    iface = machine.get_network_interface(
                                        n.get_logicalname(hw_iface))

                            if iface is None:
                                msg = "Interface %s not found on node %s, skipping configuration" % (
                                    i.device_name, machine.resource_id)
                                self.logger.warning(msg)
                                self.task.add_status_msg(
                                    msg=msg,
                                    error=True,
                                    ctx=n.name,
                                    ctx_type='node')
                                self.task.failure(focus=n.name)
                                continue

                            if iface.fabric_id == fabric.resource_id:
                                self.logger.debug(
                                    "Interface %s already attached to fabric_id %s"
                                    % (i.device_name, fabric.resource_id))
                            else:
                                self.logger.debug(
                                    "Attaching node %s interface %s to fabric_id %s"
                                    % (n.name, i.device_name,
                                       fabric.resource_id))
                                iface.attach_fabric(
                                    fabric_id=fabric.resource_id)

                            if iface.effective_mtu != nl.mtu:
                                self.logger.debug(
                                    "Updating interface %s MTU to %s" %
                                    (i.device_name, nl.mtu))
                                iface.set_mtu(nl.mtu)

                            for iface_net in getattr(i, 'networks', []):
                                dd_net = site_design.get_network(iface_net)

                                if dd_net is not None:
                                    link_iface = None
                                    if iface_net == getattr(
                                            nl, 'native_network', None):
                                        # If a node interface is attached to the native network for a link
                                        # then the interface itself should be linked to network, not a VLAN
                                        # tagged interface
                                        self.logger.debug(
                                            "Attaching node %s interface %s to untagged VLAN on fabric %s"
                                            % (n.name, i.device_name,
                                               fabric.resource_id))
                                        link_iface = iface
                                    else:
                                        # For non-native networks, we create VLAN tagged interfaces as children
                                        # of this interface
                                        vlan_options = {
                                            'vlan_tag': dd_net.vlan_id,
                                            'parent_name': iface.name,
                                        }

                                        if dd_net.mtu is not None:
                                            vlan_options['mtu'] = dd_net.mtu

                                        self.logger.debug(
                                            "Creating tagged interface for VLAN %s on system %s interface %s"
                                            % (dd_net.vlan_id, n.name,
                                               i.device_name))

                                        try:
                                            link_iface = machine.interfaces.create_vlan(
                                                **vlan_options)
                                        except errors.DriverError as ex:
                                            msg = "Error creating interface: %s" % str(
                                                ex)
                                            self.logger.info(msg)
                                            self.task.add_status_msg(
                                                msg=msg,
                                                error=True,
                                                ctx=n.name,
                                                ctx_type='node')
                                            self.task.failure(focus=n.name)
                                            continue

                                    link_options = {}
                                    link_options[
                                        'primary'] = True if iface_net == getattr(
                                            n, 'primary_network',
                                            None) else False
                                    link_options['subnet_cidr'] = dd_net.cidr

                                    found = False
                                    for a in getattr(n, 'addressing', []):
                                        if a.network == iface_net:
                                            link_options[
                                                'ip_address'] = 'dhcp' if a.type == 'dhcp' else a.address
                                            found = True

                                    if not found:
                                        msg = "No addressed assigned to network %s for node %s, link is L2 only." % (
                                            iface_net, n.name)
                                        self.logger.info(msg)
                                        self.task.add_status_msg(
                                            msg=msg,
                                            error=False,
                                            ctx=n.name,
                                            ctx_type='node')
                                        link_options['ip_address'] = None

                                    msg = "Linking system %s interface %s to subnet %s" % (
                                        n.name, i.device_name, dd_net.cidr)
                                    self.logger.info(msg)
                                    self.task.add_status_msg(
                                        msg=msg,
                                        error=False,
                                        ctx=n.name,
                                        ctx_type='node')

                                    link_iface.link_subnet(**link_options)
                                    self.task.success(focus=n.name)
                                else:
                                    self.task.failure(focus=n.name)
                                    msg = "Did not find a defined Network %s to attach to interface" % iface_net
                                    self.logger.error(msg)
                                    self.task.add_status_msg(
                                        msg=msg,
                                        error=True,
                                        ctx=n.name,
                                        ctx_type='node')
                    elif machine.status_name == 'Broken':
                        msg = ("Located node %s in MaaS, status broken. Run "
                               "ConfigureHardware before configurating network"
                               % (n.name))
                        self.logger.info(msg)
                        self.task.add_status_msg(
                            msg=msg, error=True, ctx=n.name, ctx_type='node')
                        self.task.failure(focus=n.name)
                    elif machine.status_name == 'Deployed':
                        msg = (
                            "Located node %s in MaaS, status deployed. Skipping "
                            "and considering success. Destroy node first if redeploy needed."
                            % (n.name))
                        self.logger.info(msg)
                        self.task.add_status_msg(
                            msg=msg, error=False, ctx=n.name, ctx_type='node')
                        self.task.success(focus=n.name)

                    else:
                        msg = "Located node %s in MaaS, unknown status %s. Skipping..." % (
                            n.name, machine.status_name)
                        self.logger.warning(msg)
                        self.task.add_status_msg(
                            msg=msg, error=True, ctx=n.name, ctx_type='node')
                        self.task.failure(focus=n.name)
                else:
                    msg = "Node %s not found in MaaS" % n.name
                    self.logger.warning(msg)
                    self.task.add_status_msg(
                        msg=msg, error=True, ctx=n.name, ctx_type='node')
                    self.task.failure()
            except Exception as ex:
                msg = "Error configuring network for node %s: %s" % (n.name,
                                                                     str(ex))
                self.logger.warning(msg)
                self.task.add_status_msg(
                    msg=msg, error=True, ctx=n.name, ctx_type='node')
                self.task.failure(focus=n.name)

        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.save()


class ApplyNodePlatform(BaseMaasAction):
    """Action for configuring platform settings (OS/kernel) on a node."""

    def start(self):
        try:
            machine_list = maas_machine.Machines(self.maas_client)
            machine_list.refresh()

            tag_list = maas_tag.Tags(self.maas_client)
            tag_list.refresh()
        except Exception as ex:
            self.logger.debug("Error accessing the MaaS API.", exc_info=ex)
            self.task.set_status(hd_fields.TaskStatus.Complete)
            self.task.failure()
            self.task.add_status_msg(
                msg="Error accessing MaaS API: %s" % str(ex),
                error=True,
                ctx='NA',
                ctx_type='NA')
            self.task.save()
            return

        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()

        try:
            site_design = self._load_site_design()
        except errors.OrchestratorError:
            self.task.add_status_msg(
                msg="Error loading site design.",
                error=True,
                ctx='NA',
                ctx_type='NA')
            self.task.set_status(hd_fields.TaskStatus.Complete)
            self.task.failure()
            self.task.save()
            return

        nodes = self.orchestrator.process_node_filter(self.task.node_filter,
                                                      site_design)

        for n in nodes:
            try:
                self.logger.debug(
                    "Locating node %s for platform configuration" % (n.name))

                machine = find_node_in_maas(self.maas_client, n)

                if machine is None:
                    msg = "Could not locate machine for node %s" % n.name
                    self.logger.warning(msg)
                    self.task.add_status_msg(
                        msg=msg, error=True, ctx=n.name, ctx_type='node')
                    self.task.failure(focus=n.get_id())
                    continue
            except Exception as ex1:
                msg = "Error locating machine for node %s: %s" % (n, str(ex1))
                self.task.failure(focus=n.get_id())
                self.logger.error(msg)
                self.task.add_status_msg(
                    msg=msg, error=True, ctx=n.name, ctx_type='node')
                continue

            if type(machine) is maas_rack.RackController:
                msg = ("Skipping changes to rack controller %s." % n.name)
                self.logger.info(msg)
                self.task.add_status_msg(
                    msg=msg, error=False, ctx=n.name, ctx_type='node')
                self.task.success(focus=n.name)
                continue
            elif machine.status_name == 'Deployed':
                msg = (
                    "Located node %s in MaaS, status deployed. Skipping "
                    "and considering success. Destroy node first if redeploy needed."
                    % (n.name))
                self.logger.info(msg)
                self.task.add_status_msg(
                    msg=msg, error=False, ctx=n.name, ctx_type='node')
                self.task.success(focus=n.name)
                continue

            try:
                # Render the string of all kernel params for the node
                kp_string = n.get_kernel_param_string()

                if kp_string:
                    # Check if the node has an existing kernel params tag
                    node_kp_tag = tag_list.select("%s_kp" % (n.name))
                    self.logger.info(
                        "Configuring kernel parameters for node %s" % (n.name))

                    if node_kp_tag:
                        node_kp_tag.delete()

                    msg = "Creating kernel_params tag for node %s: %s" % (
                        n.name, kp_string)
                    self.logger.debug(msg)
                    node_kp_tag = maas_tag.Tag(
                        self.maas_client,
                        name="%s_kp" % (n.name),
                        kernel_opts=kp_string)
                    node_kp_tag = tag_list.add(node_kp_tag)
                    node_kp_tag.apply_to_node(machine.resource_id)
                    self.task.add_status_msg(
                        msg=msg, error=False, ctx=n.name, ctx_type='node')

                    msg = "Applied kernel parameters to node %s" % n.name
                    self.logger.info(msg)
                    self.task.add_status_msg(
                        msg=msg, error=False, ctx=n.name, ctx_type='node')
                    self.task.success(focus=n.get_id())
                else:
                    msg = "No kernel parameters to apply for %s." % n.name
                    self.logger.debug(msg)
                    self.task.add_status_msg(
                        msg=msg, error=False, ctx=n.name, ctx_type='node')
                    self.task.success(focus=n.get_id())
            except Exception as ex2:
                msg = "Error configuring kernel parameters for node %s" % (
                    n.name)
                self.logger.error(msg + ": %s" % str(ex2))
                self.task.add_status_msg(
                    msg=msg, error=True, ctx=n.name, ctx_type='node')
                self.task.failure(focus=n.get_id())
                continue

            try:
                if n.tags is not None and len(n.tags) > 0:
                    self.logger.info(
                        "Configuring static tags for node %s" % (n.name))

                    for t in n.tags:
                        tag_list.refresh()
                        tag = tag_list.select(t)

                        if tag is None:
                            try:
                                self.logger.debug("Creating static tag %s" % t)
                                tag = maas_tag.Tag(self.maas_client, name=t)
                                tag = tag_list.add(tag)
                            except errors.DriverError:
                                tag_list.refresh()
                                tag = tag_list.select(t)
                                if tag is not None:
                                    self.logger.debug(
                                        "Tag %s arrived out of nowhere." % t)
                                else:
                                    self.logger.error(
                                        "Error creating tag %s." % t)
                                    continue

                        msg = "Applying tag %s to node %s" % (
                            tag.resource_id, machine.resource_id)
                        self.logger.debug(msg)
                        self.task.add_status_msg(
                            msg=msg, error=False, ctx=n.name, ctx_type='node')
                        tag.apply_to_node(machine.resource_id)
                    self.logger.info(
                        "Applied static tags to node %s" % (n.name))
                    self.task.success(focus=n.get_id())
                else:
                    msg = "No node tags to apply for %s." % n.name
                    self.logger.debug(msg)
                    self.task.add_status_msg(
                        msg=msg, error=False, ctx=n.name, ctx_type='node')
                    self.task.success(focus=n.get_id())
            except Exception as ex3:
                msg = "Error configuring static tags for node %s" % (n.name)
                self.logger.error(msg + ": " + str(ex3))
                self.task.add_status_msg(
                    msg=msg, error=True, ctx=n.name, ctx_type='node')
                self.task.failure(focus=n.get_id())
                continue

        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.save()
        return


class ApplyNodeStorage(BaseMaasAction):
    """Action configure node storage."""

    # NOTE(sh8121att) Partition tables take size and it seems if the first partition
    # on a block device attempts to use the full size of the device
    # MAAS will fail that the device is not large enough
    # It may be that the block device available_size does not include overhead
    # for the partition table and once the table is written, there is not
    # enough space for the 'full size' partition. So reserve the below
    # when calculating 'rest of device' sizing w/ the '>' operator
    PART_TABLE_RESERVATION = 1024 * 1024 * 4  # 4MB reservation for partition size

    def start(self):
        try:
            machine_list = maas_machine.Machines(self.maas_client)
            machine_list.refresh()
        except Exception as ex:
            self.logger.debug("Error accessing the MaaS API.", exc_info=ex)
            self.task.set_status(hd_fields.TaskStatus.Complete)
            self.task.failure()
            self.task.add_status_msg(
                msg="Error accessing MaaS API: %s" % str(ex),
                error=True,
                ctx='NA',
                ctx_type='NA')
            self.task.save()
            return

        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()

        try:
            site_design = self._load_site_design(resolve_aliases=True)
        except errors.OrchestratorError:
            self.task.add_status_msg(
                msg="Error loading site design.",
                error=True,
                ctx='NA',
                ctx_type='NA')
            self.task.set_status(hd_fields.TaskStatus.Complete)
            self.task.failure()
            self.task.save()
            return

        nodes = self.orchestrator.process_node_filter(self.task.node_filter,
                                                      site_design)

        for n in nodes:
            try:
                self.logger.debug(
                    "Locating node %s for storage configuration" % (n.name))

                machine = find_node_in_maas(self.maas_client, n)

                if machine is None:
                    msg = "Could not locate machine for node %s" % n.name
                    self.logger.warning(msg)
                    self.task.add_status_msg(
                        msg=msg, error=True, ctx=n.name, ctx_type='node')
                    self.task.failure(focus=n.get_id())
                    continue
            except Exception as ex:
                msg = "Error locating machine for node %s" % (n.name)
                self.logger.error(msg + ": " + str(ex))
                self.task.add_status_msg(
                    msg=msg, error=True, ctx=n.name, ctx_type='node')
                self.task.failure(focus=n.get_id())
                continue

            if type(machine) is maas_rack.RackController:
                msg = ("Skipping configuration updates to rack controller %s." %
                       n.name)
                self.logger.info(msg)
                self.task.add_status_msg(
                    msg=msg, error=False, ctx=n.name, ctx_type='node')
                self.task.success(focus=n.name)
                continue
            elif machine.status_name == 'Deployed':
                msg = (
                    "Located node %s in MaaS, status deployed. Skipping "
                    "and considering success. Destroy node first if redeploy needed."
                    % (n.name))
                self.logger.info(msg)
                self.task.add_status_msg(
                    msg=msg, error=False, ctx=n.name, ctx_type='node')
                self.task.success(focus=n.name)
                continue

            try:
                """
                1. Clear VGs
                2. Clear partitions
                3. Apply partitioning
                4. Create VGs
                5. Create logical volumes
                """
                msg = "Clearing current storage layout on node %s." % n.name
                self.logger.debug(msg)
                self.task.add_status_msg(
                    msg=msg, error=False, ctx=n.name, ctx_type='node')
                machine.reset_storage_config()

                (root_dev, root_block) = n.find_fs_block_device('/')
                (boot_dev, boot_block) = n.find_fs_block_device('/boot')

                storage_layout = dict()
                if isinstance(root_block, hostprofile.HostPartition):
                    storage_layout['layout_type'] = 'flat'
                    storage_layout['root_device'] = n.get_logicalname(
                        root_dev.name)
                    storage_layout['root_size'] = ApplyNodeStorage.calculate_bytes(
                        root_block.size)
                elif isinstance(root_block, hostprofile.HostVolume):
                    storage_layout['layout_type'] = 'lvm'
                    if len(root_dev.physical_devices) != 1:
                        msg = "Root LV in VG with multiple physical devices on node %s" % (
                            n.name)
                        self.logger.error(msg)
                        self.task.add_status_msg(
                            msg=msg, error=True, ctx=n.name, ctx_type='node')
                        self.task.failure(focus=n.get_id())
                        continue
                    storage_layout['root_device'] = n.get_logicalname(
                        root_dev.physical_devices[0])
                    storage_layout['root_lv_size'] = ApplyNodeStorage.calculate_bytes(
                        root_block.size)
                    storage_layout['root_lv_name'] = root_block.name
                    storage_layout['root_vg_name'] = root_dev.name

                if boot_block is not None:
                    storage_layout['boot_size'] = ApplyNodeStorage.calculate_bytes(
                        boot_block.size)

                msg = "Setting node %s root storage layout: %s" % (
                    n.name, str(storage_layout))
                self.logger.debug(msg)
                self.task.add_status_msg(
                    msg=msg, error=False, ctx=n.name, ctx_type='node')
                machine.set_storage_layout(**storage_layout)
                vg_devs = {}

                for d in n.storage_devices:
                    maas_dev = machine.block_devices.singleton({
                        'name':
                        n.get_logicalname(d.name)
                    })
                    if maas_dev is None:
                        msg = "Dev %s (%s) not found on node %s" % (
                                d.name, n.get_logicalname(d.name), n.name)
                        self.logger.warning(msg)
                        self.task.add_status_msg(
                            msg=msg, error=True, ctx=n.name, ctx_type='node')
                        self.task.failure(focus=n.get_id())
                        continue

                    if d.volume_group is not None:
                        self.logger.debug(
                            "Adding dev %s (%s) to volume group %s" %
                            (d.name, n.get_logicalname(d.name),
                             d.volume_group))
                        if d.volume_group not in vg_devs:
                            vg_devs[d.volume_group] = {'b': [], 'p': []}
                        vg_devs[d.volume_group]['b'].append(
                            maas_dev.resource_id)
                        continue

                    self.logger.debug(
                        "Partitioning dev %s (%s) on node %s" %
                        (d.name, n.get_logicalname(d.name), n.name))
                    for p in d.partitions:
                        if p.is_sys():
                            self.logger.debug(
                                "Skipping manually configuring a system partition."
                            )
                            continue
                        maas_dev.refresh()
                        size = ApplyNodeStorage.calculate_bytes(
                            size_str=p.size, context=maas_dev)
                        part = maas_partition.Partition(
                            self.maas_client, size=size, bootable=p.bootable)
                        if p.part_uuid is not None:
                            part.uuid = p.part_uuid
                        msg = "Creating partition %s sized %d bytes on dev %s (%s)" % (
                            p.name, size, d.name, n.get_logicalname(d.name))
                        self.logger.debug(msg)
                        part = maas_dev.create_partition(part)
                        self.task.add_status_msg(
                            msg=msg, error=False, ctx=n.name, ctx_type='node')

                        if p.volume_group is not None:
                            self.logger.debug(
                                "Adding partition %s to volume group %s" %
                                (p.name, p.volume_group))
                            if p.volume_group not in vg_devs:
                                vg_devs[p.volume_group] = {'b': [], 'p': []}
                            vg_devs[p.volume_group]['p'].append(
                                part.resource_id)

                        if p.mountpoint is not None:
                            format_opts = {'fstype': p.fstype}
                            if p.fs_uuid is not None:
                                format_opts['uuid'] = str(p.fs_uuid)
                            if p.fs_label is not None:
                                format_opts['label'] = p.fs_label

                            msg = "Formatting partition %s as %s" % (p.name,
                                                                     p.fstype)
                            self.logger.debug(msg)
                            part.format(**format_opts)
                            self.task.add_status_msg(
                                msg=msg,
                                error=False,
                                ctx=n.name,
                                ctx_type='node')
                            mount_opts = {
                                'mount_point': p.mountpoint,
                                'mount_options': p.mount_options,
                            }
                            msg = "Mounting partition %s on %s" % (
                                p.name, p.mountpoint)
                            self.logger.debug(msg)
                            part.mount(**mount_opts)
                            self.task.add_status_msg(
                                msg=msg,
                                error=False,
                                ctx=n.name,
                                ctx_type='node')

                self.logger.debug(
                    "Finished configuring node %s partitions" % n.name)

                for v in n.volume_groups:
                    if v.is_sys():
                        self.logger.debug(
                            "Skipping manually configuraing system VG.")
                        continue
                    if v.name not in vg_devs:
                        self.logger.warning(
                            "No physical volumes defined for VG %s, skipping."
                            % (v.name))
                        continue

                    maas_volgroup = maas_vg.VolumeGroup(
                        self.maas_client, name=v.name)

                    if v.vg_uuid is not None:
                        maas_volgroup.uuid = v.vg_uuid

                    if len(vg_devs[v.name]['b']) > 0:
                        maas_volgroup.block_devices = ','.join(
                            [str(x) for x in vg_devs[v.name]['b']])
                    if len(vg_devs[v.name]['p']) > 0:
                        maas_volgroup.partitions = ','.join(
                            [str(x) for x in vg_devs[v.name]['p']])

                    msg = "Create volume group %s on node %s" % (v.name,
                                                                 n.name)
                    self.logger.debug(msg)

                    maas_volgroup = machine.volume_groups.add(maas_volgroup)
                    maas_volgroup.refresh()
                    self.task.add_status_msg(
                        msg=msg, error=False, ctx=n.name, ctx_type='node')

                    for lv in v.logical_volumes:
                        calc_size = ApplyNodeStorage.calculate_bytes(
                            size_str=lv.size, context=maas_volgroup)
                        bd_id = maas_volgroup.create_lv(
                            name=lv.name, uuid_str=lv.lv_uuid, size=calc_size)

                        if lv.mountpoint is not None:
                            machine.refresh()
                            maas_lv = machine.block_devices.select(bd_id)
                            msg = "Formatting LV %s as filesystem on node %s." % (
                                lv.name, n.name)
                            self.logger.debug(msg)
                            self.task.add_status_msg(
                                msg=msg,
                                error=False,
                                ctx=n.name,
                                ctx_type='node')
                            maas_lv.format(
                                fstype=lv.fstype, uuid_str=lv.fs_uuid)
                            msg = "Mounting LV %s at %s on node %s." % (
                                lv.name, lv.mountpoint, n.name)
                            self.logger.debug(msg)
                            maas_lv.mount(
                                mount_point=lv.mountpoint,
                                mount_options=lv.mount_options)
                            self.task.add_status_msg(
                                msg=msg,
                                error=False,
                                ctx=n.name,
                                ctx_type='node')
                self.task.success(focus=n.get_id())
            except Exception as ex:
                self.task.failure(focus=n.get_id())
                self.task.add_status_msg(
                    msg="Error configuring storage.  %s" % str(ex),
                    error=True,
                    ctx=n.name,
                    ctx_type='node')
                self.logger.debug("Error configuring storage for node %s: %s" %
                                  (n.name, str(ex)))

        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.save()

        return

    @classmethod
    def calculate_bytes(cls, size_str=None, context=None):
        """Calculate the size on bytes of a size_str.

        Calculate the size as specified in size_str in the context of the provided
        blockdev or vg. Valid size_str format below.

        #m or #M or #mb or #MB = # * 1000 * 1000
        #g or #G or #gb or #GB = # * 1000 * 1000 * 1000
        #t or #T or #tb or #TB = # * 1000 * 1000 * 1000 * 1000
        #mi or #Mi or #mib or #MiB = # * 1024 * 1024
        #gi or #Gi or #gib or #GiB = # * 1024 * 1024 * 1024
        #ti or #Ti or #tib or #TiB = # * 1024 * 1024 * 1024 * 1024
        #% = Percentage of the total storage in the context

        Prepend '>' to the above to note the size as a minimum and the calculated size being the
        remaining storage available above the minimum

        If the calculated size is not available in the context, a NotEnoughStorage exception is
        raised.

        :param size_str: A string representing the desired size
        :param context: An instance of maasdriver.models.blockdev.BlockDevice or
                        instance of maasdriver.models.volumegroup.VolumeGroup. The
                        size_str is interpreted in the context of this device
        :return size: The calculated size in bytes
        """
        pattern = r'(>?)(\d+)([mMbBgGtTi%]{1,3})'
        regex = re.compile(pattern)
        match = regex.match(size_str)

        if not match:
            raise errors.InvalidSizeFormat(
                "Invalid size string format: %s" % size_str)

        if ((match.group(1) == '>' or match.group(3) == '%') and not context):
            raise errors.InvalidSizeFormat(
                'Sizes using the ">" or "%" format must specify a '
                'block device or volume group context')

        base_size = int(match.group(2))

        if match.group(3) in ['m', 'M', 'mb', 'MB']:
            computed_size = base_size * (1000 * 1000)
        elif match.group(3) in ['g', 'G', 'gb', 'GB']:
            computed_size = base_size * (1000 * 1000 * 1000)
        elif match.group(3) in ['t', 'T', 'tb', 'TB']:
            computed_size = base_size * (1000 * 1000 * 1000 * 1000)
        elif match.group(3) in ['mi', 'Mi', 'mib', 'MiB']:
            computed_size = base_size * (1024 * 1024)
        elif match.group(3) in ['gi', 'Gi', 'gib', 'GiB']:
            computed_size = base_size * (1024 * 1024 * 1024)
        elif match.group(3) in ['ti', 'Ti', 'tib', 'TiB']:
            computed_size = base_size * (1024 * 1024 * 1024 * 1024)
        elif match.group(3) == '%':
            computed_size = math.floor((base_size / 100) * int(context.size))

        if context and computed_size > int(context.available_size):
            raise errors.NotEnoughStorage()

        if match.group(1) == '>':
            computed_size = int(context.available_size
                                ) - ApplyNodeStorage.PART_TABLE_RESERVATION

        return computed_size


class DeployNode(BaseMaasAction):
    """Action to write persistent OS to node."""

    def start(self):
        try:
            machine_list = maas_machine.Machines(self.maas_client)
            machine_list.refresh()
        except Exception as ex:
            self.logger.debug("Error accessing the MaaS API.", exc_info=ex)
            self.task.set_status(hd_fields.TaskStatus.Complete)
            self.task.failure()
            self.task.add_status_msg(
                msg="Error accessing MaaS API: %s" % str(ex),
                error=True,
                ctx='NA',
                ctx_type='NA')
            self.task.save()
            return

        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()

        try:
            site_design = self._load_site_design()
        except errors.OrchestratorError:
            self.task.add_status_msg(
                msg="Error loading site design.",
                error=True,
                ctx='NA',
                ctx_type='NA')
            self.task.set_status(hd_fields.TaskStatus.Complete)
            self.task.failure()
            self.task.save()
            return

        nodes = self.orchestrator.process_node_filter(self.task.node_filter,
                                                      site_design)

        for n in nodes:
            try:
                machine = find_node_in_maas(self.maas_client, n)

                if type(machine) is maas_rack.RackController:
                    msg = "Skipping configuration of rack controller %s." % n.name
                    self.logger.info(msg)
                    self.task.add_status_msg(
                        msg=msg, error=False, ctx=n.name, ctx_type='node')
                    self.task.success(focus=n.name)
                    continue
                elif machine.status_name.startswith(
                        'Deployed') or machine.status_name.startswith(
                            'Deploying'):
                    msg = "Node %s already deployed or deploying, skipping." % (
                        n.name)
                    self.logger.info(msg)
                    self.task.add_status_msg(
                        msg=msg, error=False, ctx=n.name, ctx_type='node')
                    self.task.success(focus=n.name)
                    continue
                elif machine.status_name == 'Ready':
                    msg = "Acquiring node %s for deployment" % (n.name)
                    self.logger.info(msg)
                    machine = machine_list.acquire_node(n.name)
                    self.task.add_status_msg(
                        msg=msg, error=False, ctx=n.name, ctx_type='node')
                elif machine.status_name.startswith('Allocated'):
                    msg = "Node %s already acquired." % (n.name)
                    self.logger.info(msg)
                    self.task.add_status_msg(
                        msg=msg, error=False, ctx=n.name, ctx_type='node')
                else:
                    msg = "Unexpected status %s for node %s, skipping deployment." % (
                        machine.status_name, n.name)
                    self.logger.warning(msg)
                    self.task.add_status_msg(
                        msg=msg, error=True, ctx=n.name, ctx_type='node')
                    self.task.failure(focus=n.get_id())
                    continue
            except errors.DriverError as dex:
                msg = "Error acquiring node %s, skipping" % n.name
                self.logger.warning(msg, exc_info=dex)
                self.task.add_status_msg(
                    msg=msg, error=True, ctx=n.name, ctx_type='node')
                self.task.failure(focus=n.get_id())
                continue

            # Set owner data in MaaS
            try:
                self.logger.info("Setting node %s owner data." % n.name)
                for k, v in n.owner_data.items():
                    msg = "Set owner data %s = %s for node %s" % (k, v, n.name)
                    self.logger.debug(msg)
                    machine.set_owner_data(k, v)
                    self.task.add_status_msg(
                        msg=msg, error=False, ctx=n.name, ctx_type='node')
            except Exception as ex:
                msg = "Error setting node %s owner data" % n.name
                self.logger.warning(msg + ": " + str(ex))
                self.task.failure(focus=n.get_id())
                self.task.add_status_msg(
                    msg=msg, error=True, ctx=n.name, ctx_type='node')
                continue

            # Saving boot action context for a node
            self.logger.info(
                "Saving Boot Action context for node %s." % (n.name))
            try:
                ba_key = self.orchestrator.create_bootaction_context(
                    n.name, self.task)

                tag_list = maas_tag.Tags(self.maas_client)
                tag_list.refresh()
                node_id_tags = tag_list.startswith("%s__baid__" % (n.name))
                for t in node_id_tags:
                    t.delete()

                if ba_key is not None:
                    msg = "Creating boot action id key tag for node %s" % (
                        n.name)
                    self.logger.debug(msg)
                    node_baid_tag = maas_tag.Tag(
                        self.maas_client,
                        name="%s__baid__%s" % (n.name, ba_key.hex()))
                    node_baid_tag = tag_list.add(node_baid_tag)
                    node_baid_tag.apply_to_node(machine.resource_id)
                    self.task.add_status_msg(
                        msg=msg, error=False, ctx=n.name, ctx_type='node')
            except Exception as ex:
                self.logger.error(
                    "Error setting boot action id key tag for %s." % n.name,
                    exc_info=ex)

            # Extract bootaction assets that are package lists as they
            # are included in the deployment initiation

            node_packages = self.orchestrator.find_node_package_lists(
                n.name, self.task)
            user_data_dict = dict(packages=[])

            for k, v in node_packages.items():
                if v:
                    user_data_dict['packages'].append([k, v])
                else:
                    user_data_dict['packages'].append(k)

            user_data_string = None
            if user_data_dict.get('packages'):
                user_data_string = "#cloud-config\n%s" % yaml.dump(
                    user_data_dict)

            self.logger.info("Deploying node %s: image=%s, kernel=%s" %
                             (n.name, n.image, n.kernel))

            try:
                machine.deploy(
                    platform=n.image,
                    kernel=n.kernel,
                    user_data=user_data_string)
            except errors.DriverError:
                msg = "Error deploying node %s, skipping" % n.name
                self.logger.warning(msg)
                self.task.add_status_msg(
                    msg=msg, error=True, ctx=n.name, ctx_type='node')
                self.task.failure(focus=n.get_id())
                continue

            attempts = 0
            max_attempts = (
                config.config_mgr.conf.timeouts.deploy_node
                * 60) // config.config_mgr.conf.maasdriver.poll_interval

            while (attempts < max_attempts
                   and (not machine.status_name.startswith('Deployed')
                        and not machine.status_name.startswith('Failed'))):
                attempts = attempts + 1
                time.sleep(config.config_mgr.conf.maasdriver.poll_interval)
                try:
                    machine.refresh()
                    self.logger.debug(
                        "Polling node %s status attempt %d of %d: %s" %
                        (n.name, attempts, max_attempts, machine.status_name))
                except Exception:
                    self.logger.warning(
                        "Error updating node %s status during commissioning, will re-attempt."
                        % (n.name))
            if machine.status_name.startswith('Deployed'):
                msg = "Node %s deployed" % (n.name)
                self.logger.info(msg)
                self.task.add_status_msg(
                    msg=msg, error=False, ctx=n.name, ctx_type='node')
                self.task.success(focus=n.get_id())
            elif machine.status_name.startswith('Failed'):
                msg = "Node %s deployment failed" % (n.name)
                self.logger.info(msg)
                self.task.add_status_msg(
                    msg=msg, error=True, ctx=n.name, ctx_type='node')
                self.task.failure(focus=n.get_id())
            else:
                msg = "Node %s deployment timed out" % (n.name)
                self.logger.warning(msg)
                self.task.add_status_msg(
                    msg=msg, error=True, ctx=n.name, ctx_type='node')
                self.task.failure(focus=n.get_id())
            self._add_detail_logs(n, machine, 'deploy', result_type='deploy')
        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.save()

        return

def find_node_in_maas(maas_client, node_model):
    """Find a node in MAAS matching the node_model.

    Note that the returned Machine may be a simple Machine or
    a RackController.

    :param maas_client: instance of an active session to MAAS
    :param node_model: instance of objects.Node to match
    :returns: instance of maasdriver.models.Machine
    """

    machine_list = maas_machine.Machines(maas_client)
    machine_list.refresh()
    machine = machine_list.identify_baremetal_node(node_model)

    if not machine:
        # If node isn't found a normal node, check rack controllers
        rackd_list = maas_rack.RackControllers(maas_client)
        rackd_list.refresh()
        machine = rackd_list.identify_baremetal_node(node_model)

    return machine

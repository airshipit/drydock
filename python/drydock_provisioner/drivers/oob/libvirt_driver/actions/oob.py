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
"""Driver for controlling OOB interface via libvirt api."""

import time
import libvirt
from urllib.parse import urlparse

import defusedxml.ElementTree as ET

from drydock_provisioner.orchestrator.actions.orchestrator import BaseAction

import drydock_provisioner.error as errors

import drydock_provisioner.objects.fields as hd_fields


class LibvirtBaseAction(BaseAction):
    """Base action for Pyghmi executed actions."""

    def init_session(self, node):
        """Initialize a Libvirt session to the node hypervisor.

        :param node: instance of objects.BaremetalNode
        """
        if node.oob_type != 'libvirt':
            raise errors.DriverError("Node OOB type %s is not 'libvirt'" %
                                     node.oob_type)

        virsh_url = node.oob_parameters.get('libvirt_uri', None)

        if not virsh_url:
            raise errors.DriverError("Node %s has no 'libvirt_url' defined" %
                                     (node.name))

        url_parts = urlparse(virsh_url)

        if url_parts.scheme != "qemu+ssh":
            raise errors.DriverError(
                "Node %s has invalid libvirt URL scheme %s. "
                "Only 'qemu+ssh' supported." % (node.name, url_parts.scheme))

        self.logger.debug("Starting libvirt session to hypervisor %s " %
                          (virsh_url))
        virsh_ses = libvirt.open(virsh_url)

        if not virsh_ses:
            raise errors.DriverError(
                "Unable to establish libvirt session to %s." % virsh_url)

        return virsh_ses

    def set_node_pxe(self, node):
        """Set a node to PXE boot first."""
        ses = self.init_session(node)
        domain = ses.lookupByName(node.name)
        domain_xml = domain.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE
                                    | libvirt.VIR_DOMAIN_XML_INACTIVE)
        xmltree = ET.fromstring(domain_xml)

        # Delete all the current boot entries
        os_tree = xmltree.find("./os")
        boot_elements = os_tree.findall("./boot")
        for e in boot_elements:
            os_tree.remove(e)

        # Now apply our boot order which is 'network' and then 'hd'
        os_tree.append(ET.fromstring("<boot dev='network' />"))
        os_tree.append(ET.fromstring("<boot dev='hd' />"))

        # And now save the new XML def to the hypervisor
        domain_xml = ET.tostring(xmltree, encoding="utf-8")
        ses.defineXML(domain_xml.decode('utf-8'))
        ses.close()

    def get_node_status(self, node):
        """Get node status via libvirt api."""
        try:
            ses = self.init_session(node)
            domain = ses.lookupByName(node.name)
            status = domain.isActive()
        finally:
            ses.close()

        return status

    def poweroff_node(self, node):
        """Power off a node."""
        ses = self.init_session(node)
        domain = ses.lookupByName(node.name)

        if domain.isActive():
            domain.destroy()
        else:
            self.logger.debug("Node already powered off.")
            return

        try:
            i = 3
            while i > 0:
                self.logger.debug("Polling powerstate waiting for success.")
                power_state = domain.isActive()
                if not power_state:
                    return
                time.sleep(10)
                i = i - 1
            raise errors.DriverError("Power state never matched off")
        finally:
            ses.close()

    def poweron_node(self, node):
        """Power on a node."""
        ses = self.init_session(node)
        domain = ses.lookupByName(node.name)

        if not domain.isActive():
            domain.create()
        else:
            self.logger.debug("Node already powered on.")
            return

        try:
            i = 3
            while i > 0:
                self.logger.debug("Polling powerstate waiting for success.")
                power_state = domain.isActive()
                if power_state:
                    return
                time.sleep(10)
                i = i - 1
            raise errors.DriverError("Power state never matched on")
        finally:
            ses.close()


class ValidateOobServices(LibvirtBaseAction):
    """Action to validation OOB services are available."""

    def start(self):
        self.task.add_status_msg(msg="OOB does not require services.",
                                 error=False,
                                 ctx='NA',
                                 ctx_type='NA')
        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.success()
        self.task.save()

        return


class ConfigNodePxe(LibvirtBaseAction):
    """Action to configure PXE booting via OOB."""

    def start(self):
        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()

        design_status, site_design = self.orchestrator.get_effective_site(
            self.task.design_ref)
        node_list = self.orchestrator.process_node_filter(
            self.task.node_filter, site_design)

        for n in node_list:
            self.task.add_status_msg(
                msg="Libvirt doesn't configure PXE options.",
                error=True,
                ctx=n.name,
                ctx_type='node')
        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.failure()
        self.task.save()
        return


class SetNodeBoot(LibvirtBaseAction):
    """Action to configure a node to PXE boot."""

    def start(self):
        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()

        design_status, site_design = self.orchestrator.get_effective_site(
            self.task.design_ref)
        node_list = self.orchestrator.process_node_filter(
            self.task.node_filter, site_design)

        for n in node_list:
            self.logger.debug("Setting bootdev to PXE for %s" % n.name)
            self.task.add_status_msg(msg="Setting node to PXE boot.",
                                     error=False,
                                     ctx=n.name,
                                     ctx_type='node')

            try:
                self.set_node_pxe(n)
            except Exception as ex:
                self.task.add_status_msg(
                    msg="Unable to set bootdev to PXE: %s" % str(ex),
                    error=True,
                    ctx=n.name,
                    ctx_type='node')
                self.task.failure(focus=n.name)
                self.logger.warning("Unable to set node %s to PXE boot." %
                                    (n.name))
            else:
                self.task.add_status_msg(msg="Set bootdev to PXE.",
                                         error=False,
                                         ctx=n.name,
                                         ctx_type='node')
                self.logger.debug("%s reports bootdev of network" % n.name)
                self.task.success(focus=n.name)

        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.save()
        return


class PowerOffNode(LibvirtBaseAction):
    """Action to power off a node via libvirt API."""

    def start(self):
        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()

        design_status, site_design = self.orchestrator.get_effective_site(
            self.task.design_ref)
        node_list = self.orchestrator.process_node_filter(
            self.task.node_filter, site_design)

        for n in node_list:
            msg = "Shutting down domain %s" % n.name
            self.logger.debug(msg)
            self.task.add_status_msg(msg=msg,
                                     error=False,
                                     ctx=n.name,
                                     ctx_type='node')

            try:
                self.poweroff_node(n)
            except Exception as ex:
                msg = "Node failed to power off: %s" % str(ex)
                self.task.add_status_msg(msg=msg,
                                         error=True,
                                         ctx=n.name,
                                         ctx_type='node')
                self.logger.error(msg)
                self.task.failure(focus=n.name)
            else:
                msg = "Node %s powered off." % n.name
                self.task.add_status_msg(msg=msg,
                                         error=False,
                                         ctx=n.name,
                                         ctx_type='node')
                self.logger.debug(msg)
                self.task.success(focus=n.name)

        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.save()
        return


class PowerOnNode(LibvirtBaseAction):
    """Action to power on a node via libvirt API."""

    def start(self):
        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()

        design_status, site_design = self.orchestrator.get_effective_site(
            self.task.design_ref)
        node_list = self.orchestrator.process_node_filter(
            self.task.node_filter, site_design)

        for n in node_list:
            msg = "Starting domain %s" % n.name
            self.logger.debug(msg)
            self.task.add_status_msg(msg=msg,
                                     error=False,
                                     ctx=n.name,
                                     ctx_type='node')

            try:
                self.poweron_node(n)
            except Exception as ex:
                msg = "Node failed to power on: %s" % str(ex)
                self.task.add_status_msg(msg=msg,
                                         error=True,
                                         ctx=n.name,
                                         ctx_type='node')
                self.logger.error(msg)
                self.task.failure(focus=n.name)
            else:
                msg = "Node %s powered on." % n.name
                self.task.add_status_msg(msg=msg,
                                         error=False,
                                         ctx=n.name,
                                         ctx_type='node')
                self.logger.debug(msg)
                self.task.success(focus=n.name)

        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.save()
        return


class PowerCycleNode(LibvirtBaseAction):
    """Action to hard powercycle a node via IPMI."""

    def start(self):
        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()

        design_status, site_design = self.orchestrator.get_effective_site(
            self.task.design_ref)
        node_list = self.orchestrator.process_node_filter(
            self.task.node_filter, site_design)

        for n in node_list:
            msg = ("Power cycling domain for node %s" % n.name)
            self.logger.debug(msg)
            self.task.add_status_msg(msg=msg,
                                     error=False,
                                     ctx=n.name,
                                     ctx_type='node')

            try:
                self.poweroff_node(n)
                self.poweron_node(n)
            except Exception as ex:
                msg = "Node failed to power cycle: %s" % str(ex)
                self.task.add_status_msg(msg=msg,
                                         error=True,
                                         ctx=n.name,
                                         ctx_type='node')
                self.logger.error(msg)
                self.task.failure(focus=n.name)
            else:
                msg = "Node %s power cycled." % n.name
                self.task.add_status_msg(msg=msg,
                                         error=False,
                                         ctx=n.name,
                                         ctx_type='node')
                self.logger.debug(msg)
                self.task.success(focus=n.name)

        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.save()
        return


class InterrogateOob(LibvirtBaseAction):
    """Action to complete a basic interrogation of the node IPMI interface."""

    def start(self):
        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()

        design_status, site_design = self.orchestrator.get_effective_site(
            self.task.design_ref)
        node_list = self.orchestrator.process_node_filter(
            self.task.node_filter, site_design)

        for n in node_list:
            try:
                node_status = self.get_node_status(n)
            except Exception as ex:
                msg = "Node failed tatus check: %s" % str(ex)
                self.task.add_status_msg(msg=msg,
                                         error=True,
                                         ctx=n.name,
                                         ctx_type='node')
                self.logger.error(msg)
                self.task.failure(focus=n.name)
            else:
                msg = "Node %s status is %s." % (n.name, node_status)
                self.task.add_status_msg(msg=msg,
                                         error=False,
                                         ctx=n.name,
                                         ctx_type='node')
                self.logger.debug(msg)
                self.task.success(focus=n.name)

        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.save()
        return

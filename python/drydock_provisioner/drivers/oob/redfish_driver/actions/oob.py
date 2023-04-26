# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
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
"""Driver for controlling OOB interface via Redfish.

Based on Redfish Rest API specification.
"""

import time

from oslo_config import cfg

from drydock_provisioner.orchestrator.actions.orchestrator import BaseAction
from drydock_provisioner.drivers.oob.redfish_driver.client import RedfishException
from drydock_provisioner.drivers.oob.redfish_driver.client import RedfishSession

import drydock_provisioner.error as errors
import drydock_provisioner.objects.fields as hd_fields

REDFISH_MAX_ATTEMPTS = 3


class RedfishBaseAction(BaseAction):
    """Base action for Redfish executed actions."""

    def get_redfish_session(self, node):
        """Initialize a Redfish session to the node.

        :param node: instance of objects.BaremetalNode
        :return: An instance of client.RedfishSession initialized to node's Redfish interface
        """
        if node.oob_type != 'redfish':
            raise errors.DriverError("Node OOB type is not Redfish")

        oob_network = node.oob_parameters['network']
        oob_address = node.get_network_address(oob_network)
        if oob_address is None:
            raise errors.DriverError("Node %s has no OOB Redfish address" %
                                     (node.name))

        oob_account = node.oob_parameters['account']
        oob_credential = node.oob_parameters['credential']

        self.logger.debug("Starting Redfish session to %s with %s" %
                          (oob_address, oob_account))
        try:
            redfish_obj = RedfishSession(
                host=oob_address,
                account=oob_account,
                password=oob_credential,
                use_ssl=cfg.CONF.redfish_driver.use_ssl,
                connection_retries=cfg.CONF.redfish_driver.max_retries)
        except (RedfishException, errors.DriverError) as iex:
            self.logger.error(
                "Error initializing Redfish session for node %s" % node.name)
            self.logger.error("Redfish Exception: %s" % str(iex))
            redfish_obj = None

        return redfish_obj

    def exec_redfish_command(self, node, session, func, *args):
        """Call a Redfish command after establishing a session.

        :param node: Instance of objects.BaremetalNode to execute against
        :param session: Redfish session
        :param func: The redfish Command method to call
        :param args: The args to pass the func
        """
        try:
            self.logger.debug("Calling Redfish command %s on %s" %
                              (func.__name__, node.name))
            response = func(session, *args)
            return response
        except RedfishException as iex:
            self.logger.error(
                "Error executing Redfish command %s for node %s" %
                (func.__name__, node.name))
            self.logger.error("Redfish Exception: %s" % str(iex))

        raise errors.DriverError("Redfish command failed.")


class ValidateOobServices(RedfishBaseAction):
    """Action to validate OOB services are available."""

    def start(self):
        self.task.add_status_msg(msg="OOB does not require services.",
                                 error=False,
                                 ctx='NA',
                                 ctx_type='NA')
        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.success()
        self.task.save()

        return


class ConfigNodePxe(RedfishBaseAction):
    """Action to configure PXE booting via OOB."""

    def start(self):
        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()

        node_list = self.orchestrator.get_target_nodes(self.task)

        for n in node_list:
            self.task.add_status_msg(
                msg="Redfish doesn't configure PXE options.",
                error=True,
                ctx=n.name,
                ctx_type='node')
        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.failure()
        self.task.save()
        return


class SetNodeBoot(RedfishBaseAction):
    """Action to configure a node to PXE boot."""

    def start(self):
        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()

        node_list = self.orchestrator.get_target_nodes(self.task)

        for n in node_list:
            self.task.add_status_msg(msg="Setting node to PXE boot.",
                                     error=False,
                                     ctx=n.name,
                                     ctx_type='node')

            for i in range(REDFISH_MAX_ATTEMPTS):
                bootdev = None
                self.logger.debug("Setting bootdev to PXE for %s attempt #%s" %
                                  (n.name, i + 1))
                try:
                    session = self.get_redfish_session(n)
                    bootdev = self.exec_redfish_command(
                        n, session, RedfishSession.get_bootdev)
                    if bootdev.get('bootdev', '') != 'Pxe':
                        self.exec_redfish_command(n, session,
                                                  RedfishSession.set_bootdev,
                                                  'Pxe')
                        time.sleep(1)
                        bootdev = self.exec_redfish_command(
                            n, session, RedfishSession.get_bootdev)
                    session.close_session()
                except errors.DriverError as e:
                    self.logger.warning(
                        "An exception '%s' occurred while attempting to set boot device on %s"
                        % (e, n.name))

                if bootdev is not None and (bootdev.get('bootdev', '')
                                            == 'Pxe'):
                    self.task.add_status_msg(msg="Set bootdev to PXE.",
                                             error=False,
                                             ctx=n.name,
                                             ctx_type='node')
                    self.logger.debug("%s reports bootdev of network" % n.name)
                    self.task.success(focus=n.name)
                    break

                if i == REDFISH_MAX_ATTEMPTS - 1:
                    self.task.add_status_msg(
                        msg="Unable to set bootdev to PXE.",
                        error=True,
                        ctx=n.name,
                        ctx_type='node')
                    self.task.failure(focus=n.name)
                    self.logger.warning("Unable to set node %s to PXE boot." %
                                        (n.name))

        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.save()
        return


class PowerOffNode(RedfishBaseAction):
    """Action to power off a node via Redfish."""

    def start(self):
        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()

        node_list = self.orchestrator.get_target_nodes(self.task)

        for n in node_list:
            self.logger.debug("Sending set_power = off command to %s" % n.name)
            self.task.add_status_msg(msg="Sending set_power = off command.",
                                     error=False,
                                     ctx=n.name,
                                     ctx_type='node')
            session = self.get_redfish_session(n)

            # If power is already off, continue with the next node
            power_state = self.exec_redfish_command(n,
                                                    RedfishSession.get_power)
            if power_state is not None and (power_state.get('powerstate', '')
                                            == 'Off'):
                self.task.add_status_msg(msg="Node reports power off.",
                                         error=False,
                                         ctx=n.name,
                                         ctx_type='node')
                self.logger.debug(
                    "Node %s reports powerstate already off. No action required"
                    % n.name)
                self.task.success(focus=n.name)
                continue

            self.exec_redfish_command(n, session, RedfishSession.set_power,
                                      'ForceOff')

            attempts = cfg.CONF.redfish_driver.power_state_change_max_retries

            while attempts > 0:
                self.logger.debug("Polling powerstate waiting for success.")
                power_state = self.exec_redfish_command(
                    n, RedfishSession.get_power)
                if power_state is not None and (power_state.get(
                        'powerstate', '') == 'Off'):
                    self.task.add_status_msg(msg="Node reports power off.",
                                             error=False,
                                             ctx=n.name,
                                             ctx_type='node')
                    self.logger.debug("Node %s reports powerstate of off" %
                                      n.name)
                    self.task.success(focus=n.name)
                    break
                time.sleep(
                    cfg.CONF.redfish_driver.power_state_change_retry_interval)
                attempts = attempts - 1

            if power_state is not None and (power_state.get('powerstate', '')
                                            != 'Off'):
                self.task.add_status_msg(msg="Node failed to power off.",
                                         error=True,
                                         ctx=n.name,
                                         ctx_type='node')
                self.logger.error("Giving up on Redfish command to %s" %
                                  n.name)
                self.task.failure(focus=n.name)

            session.close_session()

        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.save()
        return


class PowerOnNode(RedfishBaseAction):
    """Action to power on a node via Redfish."""

    def start(self):
        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()

        node_list = self.orchestrator.get_target_nodes(self.task)

        for n in node_list:
            self.logger.debug("Sending set_power = on command to %s" % n.name)
            self.task.add_status_msg(msg="Sending set_power = on command.",
                                     error=False,
                                     ctx=n.name,
                                     ctx_type='node')
            session = self.get_redfish_session(n)

            # If power is already on, continue with the next node
            power_state = self.exec_redfish_command(n,
                                                    RedfishSession.get_power)
            if power_state is not None and (power_state.get('powerstate', '')
                                            == 'On'):
                self.task.add_status_msg(msg="Node reports power on.",
                                         error=False,
                                         ctx=n.name,
                                         ctx_type='node')
                self.logger.debug(
                    "Node %s reports powerstate already on. No action required"
                    % n.name)
                self.task.success(focus=n.name)
                continue

            self.exec_redfish_command(n, session, RedfishSession.set_power,
                                      'On')

            attempts = cfg.CONF.redfish_driver.power_state_change_max_retries

            while attempts > 0:
                self.logger.debug("Polling powerstate waiting for success.")
                power_state = self.exec_redfish_command(
                    n, session, RedfishSession.get_power)
                if power_state is not None and (power_state.get(
                        'powerstate', '') == 'On'):
                    self.logger.debug("Node %s reports powerstate of on" %
                                      n.name)
                    self.task.add_status_msg(msg="Node reports power on.",
                                             error=False,
                                             ctx=n.name,
                                             ctx_type='node')
                    self.task.success(focus=n.name)
                    break
                time.sleep(
                    cfg.CONF.redfish_driver.power_state_change_retry_interval)
                attempts = attempts - 1

            if power_state is not None and (power_state.get('powerstate', '')
                                            != 'On'):
                self.task.add_status_msg(msg="Node failed to power on.",
                                         error=True,
                                         ctx=n.name,
                                         ctx_type='node')
                self.logger.error("Giving up on Redfish command to %s" %
                                  n.name)
                self.task.failure(focus=n.name)

            session.close_session()

        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.save()
        return


class PowerCycleNode(RedfishBaseAction):
    """Action to hard powercycle a node via Redfish."""

    def start(self):
        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()

        node_list = self.orchestrator.get_target_nodes(self.task)

        for n in node_list:
            self.logger.debug("Sending set_power = off command to %s" % n.name)
            self.task.add_status_msg(msg="Power cycling node via Redfish.",
                                     error=False,
                                     ctx=n.name,
                                     ctx_type='node')
            session = self.get_redfish_session(n)
            self.exec_redfish_command(n, session, RedfishSession.set_power,
                                      'ForceOff')

            # Wait for power state of off before booting back up
            attempts = cfg.CONF.redfish_driver.power_state_change_max_retries

            while attempts > 0:
                power_state = self.exec_redfish_command(
                    n, session, RedfishSession.get_power)
                if power_state is not None and power_state.get(
                        'powerstate', '') == 'Off':
                    self.logger.debug("%s reports powerstate of off" % n.name)
                    break
                elif power_state is None:
                    self.logger.debug(
                        "No response on Redfish power query to %s" % n.name)
                time.sleep(
                    cfg.CONF.redfish_driver.power_state_change_retry_interval)
                attempts = attempts - 1

            if power_state.get('powerstate', '') != 'Off':
                self.task.add_status_msg(
                    msg="Failed to power down during power cycle.",
                    error=True,
                    ctx=n.name,
                    ctx_type='node')
                self.logger.warning(
                    "Failed powering down node %s during power cycle task" %
                    n.name)
                self.task.failure(focus=n.name)
                break

            self.logger.debug("Sending set_power = on command to %s" % n.name)
            self.exec_redfish_command(n, session, RedfishSession.set_power,
                                      'On')

            attempts = cfg.CONF.redfish_driver.power_state_change_max_retries

            while attempts > 0:
                power_state = self.exec_redfish_command(
                    n, session, RedfishSession.get_power)
                if power_state is not None and power_state.get(
                        'powerstate', '') == 'On':
                    self.logger.debug("%s reports powerstate of on" % n.name)
                    break
                elif power_state is None:
                    self.logger.debug(
                        "No response on Redfish power query to %s" % n.name)
                time.sleep(
                    cfg.CONF.redfish_driver.power_state_change_retry_interval)
                attempts = attempts - 1

            if power_state is not None and (power_state.get('powerstate', '')
                                            == 'On'):
                self.task.add_status_msg(msg="Node power cycle complete.",
                                         error=False,
                                         ctx=n.name,
                                         ctx_type='node')
                self.task.success(focus=n.name)
            else:
                self.task.add_status_msg(
                    msg="Failed to power up during power cycle.",
                    error=True,
                    ctx=n.name,
                    ctx_type='node')
                self.logger.warning(
                    "Failed powering up node %s during power cycle task" %
                    n.name)
                self.task.failure(focus=n.name)

            session.close_session()

        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.save()
        return


class InterrogateOob(RedfishBaseAction):
    """Action to complete a basic interrogation of the node Redfish interface."""

    def start(self):
        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()

        node_list = self.orchestrator.get_target_nodes(self.task)

        for n in node_list:
            try:
                self.logger.debug("Interrogating node %s Redfish interface." %
                                  n.name)
                session = self.get_redfish_session(n)
                powerstate = self.exec_redfish_command(
                    n, session, RedfishSession.get_power)
                session.close_session()
                if powerstate is None:
                    raise errors.DriverError()
                self.task.add_status_msg(
                    msg="Redfish interface interrogation yielded powerstate %s"
                    % powerstate.get('powerstate'),
                    error=False,
                    ctx=n.name,
                    ctx_type='node')
                self.task.success(focus=n.name)
            except errors.DriverError:
                self.logger.debug(
                    "Interrogating node %s Redfish interface failed." % n.name)
                self.task.add_status_msg(
                    msg="Redfish interface interrogation failed.",
                    error=True,
                    ctx=n.name,
                    ctx_type='node')
                self.task.failure(focus=n.name)

        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.save()
        return

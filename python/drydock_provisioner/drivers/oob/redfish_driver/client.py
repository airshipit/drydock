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
"""Redfish object to provide commands.

Uses Redfish client to communicate to node.
"""

from redfish import AuthMethod, redfish_client
from redfish.rest.v1 import ServerDownOrUnreachableError
from redfish.rest.v1 import InvalidCredentialsError
from redfish.rest.v1 import RetriesExhaustedError

class RedfishSession(object):
    """Redfish Client to provide OOB commands"""

    def __init__(self, host, account, password, use_ssl=True, connection_retries=10):
        try:
            if use_ssl:
                redfish_url = 'https://' + host
            else:
                redfish_url = 'http://' + host
            self.redfish_client = redfish_client(base_url=redfish_url,
                                                 username=account,
                                                 password=password)

            self.redfish_client.MAX_RETRY = connection_retries
            self.redfish_client.login(auth=AuthMethod.SESSION)
        except RetriesExhaustedError:
            raise RedfishException("Login failed: Retries exhausted")
        except InvalidCredentialsError:
            raise RedfishException("Login failed: Invalid credentials")
        except ServerDownOrUnreachableError:
            raise RedfishException("Login failed: Server unreachable")

    def __del__(self):
        self.redfish_client.logout()

    def close_session(self):
        self.redfish_client.logout()

    def get_system_instance(self):
        response = self.redfish_client.get("/redfish/v1/Systems")

        if response.status != 200:
            raise RedfishException(response._read)

        # Assumption that only one system is available on Node
        if response.dict["Members@odata.count"] != 1:
            raise RedfishException("Number of systems are more than one in the node")
        instance = response.dict["Members"][0]["@odata.id"]

        return instance

    def get_bootdev(self):
        """Get current boot type information from Node.

        :raises: RedfishException on an error
        :return: dict -- response will return as dict in format of
                 {'bootdev': bootdev}
        """
        instance = self.get_system_instance()
        response = self.redfish_client.get(path=instance)

        if response.status != 200:
            raise RedfishException(response._read)

        bootdev = response.dict["Boot"]["BootSourceOverrideTarget"]
        return {'bootdev': bootdev}

    def set_bootdev(self, bootdev, **kwargs):
        """Set boot type on the Node for next boot.

        :param bootdev: Boot source for the next boot
                        * None - Boot from the normal boot device.
                        * Pxe - Boot from network
                        * Cd - Boot from CD/DVD disc
                        * Usb - Boot from USB device specified by system BIOS
                        * Hdd - Boot from Hard drive
                        * BiosSetup - Boot to bios setup utility
                        * Utilities - Boot manufacurer utlities program
                        * UefiTarget - Boot to the UEFI Device specified in the
                                       UefiTargetBootSourceOverride property
                        * UefiShell - Boot to the UEFI Shell
                        * UefiHttp - Boot from UEFI HTTP network location
        :param **kwargs: To specify extra arguments for a given bootdev
                         Example to specify UefiTargetBootSourceOverride value
                         for bootdev UefiTarget
        :raises: RedfishException on an error
        :return: dict -- response will return as dict in format of
                 {'bootdev': bootdev}
        """
        instance = self.get_system_instance()

        payload = {
            "Boot": {
                "BootSourceOverrideEnabled": "Once",
                "BootSourceOverrideTarget": bootdev,
            }
        }

        if bootdev == 'UefiTarget':
            payload['Boot']['UefiTargetBootSourceOverride'] = kwargs.get(
                'UefiTargetBootSourceOverride', '')

        response = self.redfish_client.patch(path=instance, body=payload)
        if response.status != 200:
            raise RedfishException(response._read)

        return {'bootdev': bootdev}

    def get_power(self):
        """Get current power state information from Node.

        :raises: RedfishException on an error
        :return: dict -- response will return as dict in format of
                 {'powerstate': powerstate}
        """
        instance = self.get_system_instance()

        response = self.redfish_client.get(path=instance)
        if response.status != 200:
            raise RedfishException(response._read)

        powerstate = response.dict["PowerState"]
        return {'powerstate': powerstate}

    def set_power(self, powerstate):
        """Request power change on the node.

        :param powerstate: set power change
                           * On - Power On the unit
                           * ForceOff - Turn off immediately (non graceful)
                           * PushPowerButton - Simulate pressing physical
                                               power button
                           * GracefulRestart - Perform a graceful shutdown
                                               and then start

        :raises: RedfishException on an error
        :return: dict -- response will return as dict in format of
                 {'powerstate': powerstate}
        """
        instance = self.get_system_instance()

        if powerstate not in ["On", "ForceOff", "PushPowerButton", "GracefulRestart"]:
            raise RedfishException("Unsupported powerstate")

        current_state = self.get_power()
        if (powerstate == "On" and current_state["powerstate"] == "On") or \
           (powerstate == "ForceOff" and current_state["powerstate"] == "Off"):
            return {'powerstate': powerstate}

        payload = {
            "ResetType": powerstate
        }

        url = instance + "/Actions/ComputerSystem.Reset"
        response = self.redfish_client.post(path=url, body=payload)
        if response.status in [200, 201, 204]:
            return {'powerstate': powerstate}
        else:
            raise RedfishException(response._read)


class RedfishException(Exception):
    """Redfish Exception with error in message"""
    pass

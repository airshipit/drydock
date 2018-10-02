# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
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
"""Errors and exceptions specific to MAAS node driver."""
import drydock_provisioner.error as errors


class RackControllerConflict(errors.DriverError):
    """Exception for settings that are not allowed because not enough
       or too many rack controllers are attached to a network."""
    pass


class ApiNotAvailable(errors.DriverError):
    """Exception when trying to utilize the MAAS API and the connection
       fails."""
    pass

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
import drydock_provisioner.drivers.node.maasdriver.models.base as model_base
import drydock_provisioner.drivers.node.maasdriver.models.iprange as maas_iprange
import drydock_provisioner.drivers.node.maasdriver.models.staticroute as maas_route


class Subnet(model_base.ResourceBase):
    """Model for a subnet."""

    resource_url = 'subnets/{resource_id}/'
    fields = [
        'resource_id', 'name', 'description', 'fabric', 'vlan', 'vid', 'cidr',
        'gateway_ip', 'rdns_mode', 'allow_proxy', 'dns_servers'
    ]
    json_fields = [
        'name', 'description', 'vlan', 'cidr', 'gateway_ip', 'rdns_mode',
        'allow_proxy', 'dns_servers'
    ]

    def __init__(self, api_client, **kwargs):
        super(Subnet, self).__init__(api_client, **kwargs)

    def add_address_range(self, addr_range):
        """
        Add a reserved or dynamic (DHCP) address range to this subnet

        :param addr_range: Dict with keys 'type', 'start', 'end'
        """

        # TODO Do better overlap detection. For now we just check if the exact range exists
        current_ranges = maas_iprange.IpRanges(self.api_client)
        current_ranges.refresh()

        exists = current_ranges.query({
            'start_ip': addr_range.get('start', None),
            'end_ip': addr_range.get('end', None)
        })

        if len(exists) > 0:
            self.logger.info(
                'Address range from %s to %s already exists, skipping.' %
                (addr_range.get('start', None), addr_range.get('end', None)))
            return

        # Static ranges are what is left after reserved (not assigned by MaaS)
        # and DHCP ranges are removed from a subnet
        if addr_range.get('type', None) in ['reserved', 'dhcp']:
            range_type = addr_range.get('type', None)

            if range_type == 'dhcp':
                range_type = 'dynamic'

            maas_range = maas_iprange.IpRange(
                self.api_client,
                comment="Configured by Drydock",
                subnet=self.resource_id,
                type=range_type,
                start_ip=addr_range.get('start', None),
                end_ip=addr_range.get('end', None))
            maas_ranges = maas_iprange.IpRanges(self.api_client)
            maas_ranges.add(maas_range)

    def add_static_route(self, dest_subnet, gateway, metric=100):
        """Add a static route to ``dest_subnet`` via ``gateway`` to this source subnet.

        :param dest_subnet: maas resource_id of the destination subnet
        :param gateway: string IP address of the nexthop gateway
        :param metric: weight to assign this gateway
        """
        sr = maas_route.StaticRoutes(self.api_client)
        sr.refresh()
        current_route = sr.singleton({
            'source': self.resource_id,
            'destination': dest_subnet
        })
        if current_route is not None:
            current_route.delete()

        new_route = maas_route.StaticRoute(self.api_client,
                                           source=self.resource_id,
                                           destination=dest_subnet,
                                           gateway_ip=gateway,
                                           metric=metric)
        new_route = sr.add(new_route)
        return new_route

    @classmethod
    def from_dict(cls, api_client, obj_dict):
        """
        Because MaaS decides to replace the VLAN id with the
        representation of the VLAN, we must reverse it for a true
        representation of the resource
        """
        refined_dict = {k: obj_dict.get(k, None) for k in cls.fields}
        if 'id' in obj_dict.keys():
            refined_dict['resource_id'] = obj_dict.get('id')

        if isinstance(refined_dict.get('vlan', None), dict):
            refined_dict['fabric'] = refined_dict['vlan']['fabric_id']
            refined_dict['vlan'] = refined_dict['vlan']['id']

        i = cls(api_client, **refined_dict)
        return i


class Subnets(model_base.ResourceCollectionBase):
    """Model for collection of subnets."""

    collection_url = 'subnets/'
    collection_resource = Subnet

    def __init__(self, api_client, **kwargs):
        super(Subnets, self).__init__(api_client)

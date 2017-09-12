=======================
Authoring Site Topology
=======================

Drydock uses a YAML-formatted site topology definition to configure
downstream drivers to provision baremetal nodes. This topology describes
the networking configuration of a site as well as the set of node configurations
that will be deployed. A node configuration consists of network attachment,
network addressing, local storage, kernel selection and configuration and
metadata.

The best source for a sample of the YAML schema for a topology is the unit
test input source_ /tests/yaml_samples/fullsite.yaml in tests/yaml_samples/fullsite.yaml.

Defining Networking
===================

Network definitions in the topology are described by two document types: NetworkLink and
Network. NetworkLink describes a physical or logical link between a node and switch. It
is concerned with attributes that must be agreed upon by both endpoints: bonding, media
speed, trunking, etc. A Network describes the layer 2 and layer 3 networks accessible
over a link.

Network Links
-------------

The NetworkLink document defines layer 1 and layer 2 attributes that should be in-sync
between the node and the switch. Each link can support a single untagged VLAN and 0 or more
tagged VLANs.

Example YAML schema of the NetworkLink spec::

    spec:
      bonding:
        mode: 802.3ad
        hash: layer3+4
        peer_rate: slow
      mtu: 9000
      linkspeed: auto
      trunking:
        mode: 802.1q
      allowed_networks:
        - public
        - mgmt

``bonding`` describes combining multiple physical links into a single logical link (aka LAG
or link aggregation group).

* ``mode``: What bonding mode to configure

    * ``disabled``: Do not configure a bond
    * ``802.3ad``: Use 802.3ad dynamic aggregation (aka LACP)
    * ``active-backup``: Use static active/standby bonding
    * ``balanced-rr``: Use static round-robin bonding

For a ``mode`` of ``802.3ad`` the below attributes are available, but optional.

* ``hash``: The link selection hash. Supported values are ``layer3+4``, ``layer2+3``, ``layer2``. Default is ``layer3+4``
* ``peer_rate``: How frequently to send LACP control frames. Supported values are ``fast`` and ``slow``. Default is ``fast``
* ``mon_rate``: Interval between checking link state in milliseconds. Default is ``100``
* ``up_delay``: Delay in milliseconds between a link coming up and being marked up in the bond. Must be greater than ``mon_rate``. Default is ``200``
* ``down_delay``: Delay in milliseconds between a link going down and being marked down in the bond.  Must be greater than ``mon_rate``. Default is ``200``

``mtu`` is the maximum transmission unit for the link. It must be equal or greater than the MTU of any VLAN interfaces
using the link. Default is ``1500``.

``linkspeed`` is the physical layer speed and duplex. Recommended to always be ``auto``

``trunking`` describes how multiple layer 2 networks will be multiplexed on the link.

    * ``mode``: Can be ``disabled`` for no trunking or ``802.1q`` for standard VLAN tagging
    * ``default_network``: For ``mode: disabled``, this is the single network on the link. For ``mode: 802.1q`` this is optionally the network accessed by untagged frames.

``allowed_networks`` is a sequence of network names listing all networks allowed on this link. Each Network can
be listed on one and only one NetworkLink.

Network
-------

The Network document defines the layer 2 and layer 3 networks nodes will access. Each Network is accessible over
exactly one NetworkLink. However that NetworkLink can be attached to different interfaces on different nodes
to support changing hardware configurations.

Example YAML schema of the Network spec::

    spec:
      vlan: '102'
      mtu: 1500
      cidr: 172.16.3.0/24
      ranges:
        - type: static
          start: 172.16.3.15
          end: 172.16.3.200
        - type: dhcp
          start: 172.16.3.201
          end: 172.16.3.254
      routes:
        - subnet: 0.0.0.0/0
          gateway: 172.16.3.1
          metric: 10
      dns:
        domain: sitename.example.com
        servers: 8.8.8.8

If a Network is accessible over a NetworkLink using 802.1q VLAN tagging, the ``vlan`` attribute
specified the VLAN tag for this Network. It should be omitted for non-tagged Networks.

``mtu`` is the maximum transmission unit for this Network. Must be equal or less than the ``mtu``
defined for the hosting NetworkLink. Can be omitted to default to the NetworkLink ``mtu``.

``cidr`` is the classless inter-domain routing address for the network.

``ranges`` defines a sequence of IP addresses within the defined ``cidr``. Ranges cannot overlap.

* ``type``: The type of address range.

    * ``static``: A range used for static, explicit address assignments for nodes.
    * ``dhcp``: A range used for assigning DHCP addresses. Note that a network being used for PXE booting must have a DHCP range defined.
    * ``reserved``: A range of addresses that will not be used by MaaS.

* ``start``: The starting IP of the range, inclusive.
* ``end``: The last IP of the range, inclusive

*NOTE: Static routes is not currently implemented beyond specifying a route for 0.0.0.0/0 for default route*
``routes`` defines a list of static routes to be configured on nodes attached to this network.

* ``subnet``: Destination CIDR for the route
* ``gateway``: The gateway IP on this Network to use for accessing the destination
* ``metric``: The metric or weight for this route

``dns`` is used for specifying the list of DNS servers to use if this network
is the priamry network for the node.

* ``servers``: A comma-separated list of IP addresses to use for DNS resolution
* ``domain``: A domain that can be used for automated registeration of IP addresses assigned from this Network

DHCP Relay
~~~~~~~~~~

DHCP relaying is used when a DHCP server is not attached to the same layer 2 broadcast domain as nodes that
are being PXE booted. The DHCP requests from the node are consumed by the relay (generally configured on a
top-of-rack switch) which then enscapsulates the request in layer 3 routing and sends it to an upstream DHCP
server. The Network spec supports a ``dhcp_relay`` key for Networks that should relay DHCP requests.

* The Network must have a configured DHCP relay, this is *not* configured by Drydock or MaaS.
* The ``upstream_target`` IP address must be a host IP address for a MaaS rack controller
* The Network must have a defined DHCP address range.
* The upstream target network must have a defined DHCP address range.

The ``dhcp_relay`` stanza::

    dhcp_relay:
      upstream_target: 172.16.4.100

Defining Node Configuration
===========================

Node configuration is defined in three documents: HostProfile, HardwareProfile and BaremetalNode. HardwareProfile
defines attributes directly related to hardware configuration such as card-slot layout and firmware levels. HostProfile
is a generic definition for how a node should be configured such that many nodes can reference a single HostProfile
and each will be configured identically. A BaremetalNode is a concrete reference to particular physical node.
The BaremetalNode definition will reference a HostProfile and can then extend or override any of the configuration values.

Example HostProfile and BaremetalNode configuration::

    ---
    apiVersion: 'drydock/v1'
    kind: HostProfile
    metadata:
      name: defaults
      region: sitename
      date: 17-FEB-2017
      author: sh8121@att.com
    spec:
      # configuration values
    ---
    apiVersion: 'drydock/v1'
    kind: HostProfile
    metadata:
      name: compute_node
      region: sitename
      date: 17-FEB-2017
      author: sh8121@att.com
    spec:
      host_profile: defaults
      # compute_node customizations to defaults
    ---
    apiVersion: 'drydock/v1'
    kind: BaremetalNode
    metadata:
      name: compute01
      region: sitename
      date: 17-FEB-2017
      author: sh8121@att.com
    spec:
      host_profile: compute_node
      # configuration customization specific to single node compute01
    ...

In the above example, the ``compute_node`` HostProfile adopts all values from the ``defaults``
HostProfile and can then override defined values or append additional values. BaremetalNode
``compute01`` then adopts all values from the ``compute_node`` HostProfile (which includes all
the configuration items it adopted from ``defaults``) and can then again override or append any
configuration that is specific to that node.

Defining Node Interfaces and Network Addressing
===============================================

Node network attachment can be described in a HostProfile or a BaremetalNode document. Node addressing
is allowed only in a BaremetalNode document. If a HostProfile or BaremetalNode needs to remove a defined
interface from an inherited configuration, it can set the mapping value for the interface name to ``null``.

Once the interface attachments to networks is defined, HostProfile and BaremetalNode specs must define a
``primary_network`` attribute to denote which network the node should use a the primary route. This designation

Interfaces
----------

Interfaces for a node can be described in either a HostProfile or BaremetalNode definition. This will attach
a defined NetworkLink to a host interface and define which Networks should be configured to use that interface.

Example interface definition YAML schema::

    interfaces:
      pxe:
        device_link: pxe
        labels:
          pxe: true
        slaves:
          - prim_nic01
        networks:
          - pxe
      bond0:
        device_link: gp
        slaves:
          - prim_nic01
          - prim_nic02
        networks:
          - mgmt
          - private

Each key in the interfaces mapping is a defined interface. The key is the name that will be used
on the deployed node for the interface. The value must be a mapping defining the interface configuration
or ``null`` to denote removal of that interface for an inherited configuration.

* ``device_link``: The name of the defined NetworkLink that will be attached to this interface. The NetworkLink
  definition includes part of the interface configuration such as bonding.
* ``labels``: Metadata for describing this interface.
* ``slaves``: The list of hardware interfaces used for creating this interface. This value can be a device alias
  defined in the HardwareProfile or the kernel name of the hardware interface. For bonded interfaces, this would
  list all the slaves. For non-bonded interfaces, this should list the single hardware interface used.
* ``networks``: This is the list of networks to enable on this interface. If multiple networks are listed, the
  NetworkLink attached to this interface must have trunking enabled or the design validation will fail.

Addressing
----------

Addressing for a node can only be defined in a BaremetalNode definition. The ``addressing`` stanza simply
defines a static IP address or ``dhcp`` for each network a node should have a configured layer 3 interface on. It
is a valid design to omit networks from the ``addressing`` stanza, in that case the interface attached to the omitted
network will be configured as link up with no address.

Example ``addressing`` YAML schema::

  addressing:
    - network: pxe
      address: dhcp
    - network: mgmt
      address: 172.16.1.21
    - network: private
      address: 172.16.2.21
    - network: oob
      address: 172.16.100.21


Defining Node Storage
=====================

Storage can be defined in the ``storage`` stanza of either a HostProfile or BaremetalNode
document. The storage configuration can describe creation of partitions on physical disks,
the assignment of physical disks and/or partitions to volume groups, and the creation of
logical volumes. Drydock will make a best effort to parse out system-level storage such
as the root filesystem or boot filesystem and take appropriate steps to configure them in
the active node provisioning driver. At a minimum the storage configuration *must* contain
a root filesystem partition.

Example YAML schema of the ``storage`` stanza::

    storage:
      physical_devices:
        sda:
          labels:
            bootdrive: true
          partitions:
            - name: 'root'
              size: '10g'
              bootable: true
              filesystem:
                mountpoint: '/'
                fstype: 'ext4'
                mount_options: 'defaults'
            - name: 'boot'
              size: '1g'
              filesystem:
                mountpoint: '/boot'
                fstype: 'ext4'
                mount_options: 'defaults'
        sdb:
          volume_group: 'log_vg'
      volume_groups:
        log_vg:
          logical_volumes:
            - name: 'log_lv'
              size: '500m'
              filesystem:
                mountpoint: '/var/log'
                fstype: 'xfs'
                mount_options: 'defaults'

Schema
------

The ``storage`` stanza can contain two top level keys: ``physical_devices`` and
``volume_groups``. The latter is optional.

Physical Devices and Partitions
-------------------------------

A physical device can either be carved up in partitions (including a single partition
consuming the entire device) or added to a volume group as a physical volume. Each
key in the ``physical_devices`` mapping represents a device on a node. The key should either
be a device alias defined in the HardwareProfile or the name of the device published
by the OS. The value of each key must be a mapping with the following keys

* ``labels``: A mapping of key/value strings providing generic labels for the device
* ``partitions``: A sequence of mappings listing the partitions to be created on the device. The mapping is described below. Incompatible with the ``volume_group`` specification.
* ``volume_group``: A volume group name to add the device to as a physical volume. Incompatible with the ``partitions`` specification.

Partition
~~~~~~~~~

A partition mapping describes a GPT partition on a physical disk. It can left as a raw
block device or formatted and mounted as a filesystem

* ``name``: Metadata describing the partition in the topology
* ``size``: The size of the partition. See the *Size Format* section below
* ``bootable``: Boolean whether this partition should be the bootable device
* ``part_uuid``: A UUID4 formatted UUID to assign to the partition. If not specified one will be generated
* ``filesystem``: A optional mapping describing how the partition should be formatted and mounted

    * ``mountpoint``: Where the filesystem should be mounted. If not specified the partition will be left as a raw deice
    * ``fstype``: The format of the filesyste. Defaults to ext4
    * ``mount_options``: fstab style mount options. Default is 'defaults'
    * ``fs_uuid``: A UUID4 formatted UUID to assign to the filesystem. If not specified one will be generated
    * ``fs_label``: A filesystem label to assign to the filesystem. Optional.

Size Format
~~~~~~~~~~~

The size specification for a partition or logical volume is formed from three parts

* The first character can optionally be ``>`` indicating that the size specified is a minimum and the calculated size should be at least the minimum and should take the rest of the available space on the physical device or volume group.
* The second part is the numeric portion and must be an integer
* The third part is a label

    * ``m``\|``M``\|``mb``\|``MB``: Megabytes or 10^6 * the numeric
    * ``g``\|``G``\|``gb``\|``GB``: Gigabytes or 10^9 * the numeric
    * ``t``\|``T``\|``tb``\|``TB``: Terabytes or 10^12 * the numeric
    * ``%``: The percentage of total device or volume group space

Volume Groups and Logical Volumes
---------------------------------

Logical volumes can be used to create RAID-0 volumes spanning multiple physical disks or partitions.
Each key in the ``volume_groups`` mapping is a name assigned to a volume group. This name must be specified
as the ``volume_group`` attribute on one or more physical devices or partitions, or the configuration is invalid.
Each mapping value is another mapping describing the volume group.

* ``vg_uuid``: A UUID4 format uuid applied to the volume group. If not specified, one is generated
* ``logical_volumes``: A sequence of mappings listing the logical volumes to be created in the volume group

Logical Volume
~~~~~~~~~~~~~~

A logical volume is a RAID-0 volume. Using logical volumes for ``/`` and ``/boot`` is supported

* ``name``: Required field. Used as the logical volume name.
* ``size``: The logical volume size. See *Size Format* above for details.
* ``lv_uuid``: A UUID4 format uuid applied to the logical volume: If not specified, one is generated
* ``filesystem``: A mapping specifying how the logical volume should be formatted and mounted. See the *Partition* section above for filesystem details.


